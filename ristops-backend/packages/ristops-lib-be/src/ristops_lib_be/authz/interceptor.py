import logging
from http import HTTPStatus
from typing import Callable, Awaitable

from fastapi import FastAPI, HTTPException, Request
from starlette import status

from ristops_lib_be.authz.policy import Policy, POLICY
from ristops_lib_core.app.routes import RouteAttributeRegistry
from ristops_lib_core.auth.authn import PublicRoutesRegistry
from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.schema.authz import CheckAuthorizationRequest, AuthorizationGrant

_logger = logging.getLogger(__name__)
Authorizer = Callable[[CheckAuthorizationRequest], Awaitable[bool]]


async def policy_to_grant(request: Request, policies: tuple[Policy, ...]) -> list[AuthorizationGrant]:
    return [
        await _policy(request)
        for _policy in policies
    ]


class AuthZInterceptor:
    """
    Dependency interceptor used to authorize requests.

    This callable object must be added as dependency to FastAPI app.router.dependencies before routers
    registration. It is not used as middleware because authorizers need access to a structured request
    object. After registering routers, ``register`` must be called so the interceptor can build its
    route index.

    Authorization is **deny-by-default**:

    1. Routes decorated with ``@public`` -> skip (authentication already waived by AuthNMiddleware).
    2. Every other route MUST carry a ``@policy`` decorator.  Omitting it raises ``RuntimeError``
       (developer error → 500).
    3. ``@policy()`` with no arguments -> any authenticated user is allowed through.
    4. ``@policy(Policy(…))`` -> ACL check enforced against the authz service.
    """

    def __init__(self, authorizer: Authorizer) -> None:
        self._authorizer = authorizer
        self._protected_routes: RouteAttributeRegistry[tuple[Policy, ...]] | None = None
        self._public_registry: PublicRoutesRegistry | None = None

    def register(self, api: FastAPI) -> None:
        """Build route indexes. Must be called after all routers have been registered."""
        # we might want to monkeypatch FastAPI.include_routers in order to make this operation automatic
        self._protected_routes = RouteAttributeRegistry[tuple[Policy, ...]](api, POLICY)
        self._public_registry = PublicRoutesRegistry(api)

    async def __call__(self, request: Request) -> None:
        try:
            return await self._do_call(request)
        except HTTPException:
            # managed, re-raise as-is
            raise
        except Exception as e:
            _logger.error("Failed to authorize request")
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Failed to authorize request",
            ) from e

    async def _do_call(self, request: Request) -> None:
        if self._protected_routes is None or self._public_registry is None:
            _logger.error("AuthZInterceptor.register() has not been called")
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

        if self._public_registry.is_public(request):
            # route is @public: authentication was already waived -> skip authorization
            return None

        policies: tuple[Policy, ...] | None = self._protected_routes.get(request.scope)
        if policies is None:
            # route exists but has no @policy
            _logger.error(
                "Route %s %s has no @policy decorator. Every non-public route must declare its authorization policy.",
                request.method, request.url.path
            )
            raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR)

        if len(policies) == 0:
            # @policy() with no arguments -> no authorization required
            return None

        # enforce ACL
        user_id = APP_CONTEXT.get(ContextKey.USER_ID)
        if user_id is None:
            # unexpected state: user should be set -> forbid the operation
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user",
            )
        grants = await policy_to_grant(request, policies)
        authz_request = CheckAuthorizationRequest(
            user_id=user_id,
            grants=grants,
        )
        is_authorized = await self._authorizer(authz_request)
        if not is_authorized:
            _logger.error("Authorization failed for request: %s", authz_request)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not authorized to perform this action",
            )
        return None

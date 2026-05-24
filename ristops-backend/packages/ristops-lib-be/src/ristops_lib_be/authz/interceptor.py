import logging
from http import HTTPStatus
from typing import Callable, Awaitable

from fastapi import FastAPI, HTTPException, Request
from starlette import status

from ristops_lib_be.authz.policy import Policy, POLICY
from ristops_lib_core.app.routes import RouteAttributeRegistry
from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.schema.authz import CheckAuthorizationRequest, AuthorizationGrant

_logger = logging.getLogger(__name__)
Authorizer = Callable[[CheckAuthorizationRequest], Awaitable[bool]]


async def _policy_to_grant(request: Request, policies: list[Policy]) -> list[AuthorizationGrant]:
    return [
        await _policy(request)
        for _policy in policies
    ]


class AuthZInterceptor:
    """
    Dependency interceptor used to authorize requests.
    This callable object must be added as dependency to FastAPI app.router.dependencies before routers registration.
    It's not used a middleware for authorization, because authorizers needs to access a more structured request object.
    After registering routers, the register method should be called to register all protected routes.
    """

    def __init__(self, authorizer: Authorizer) -> None:
        self._authorizer = authorizer
        self._protected_routes: RouteAttributeRegistry[list[Policy]] | None = None

    def register(self, api: FastAPI) -> None:
        """ Register protected routes. This method must be called after routers registration. """
        # we might want to monkeypatch FastAPI.include_routers in order to make this operation authomatic
        self._protected_routes = RouteAttributeRegistry[list[Policy]](api, POLICY)

    async def __call__(self, request: Request) -> None:
        try:
            return await self._do_call(request)
        except HTTPException:
            # managed: re-raise
            raise
        except Exception as e:
            _logger.error("Failed to authorize request")
            raise HTTPException(
                status_code=HTTPStatus.FORBIDDEN,
                detail="Failed authorize request"
            ) from e

    async def _do_call(self, request: Request) -> None:
        if self._protected_routes is None:
            raise ValueError("Authorization interceptor is not initialized")
        policies: list[Policy] = self._protected_routes.get(request.scope, [])
        if not policies:
            # not annotated or empty
            return None
        user_id = APP_CONTEXT.get(ContextKey.USER_ID)
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user"
            )
        grants = await _policy_to_grant(request, policies)
        authz_request = CheckAuthorizationRequest(
            user_id=user_id,
            grants=grants
        )
        is_authorized = await self._authorizer(authz_request)
        if not is_authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not authorized to perform this action"
            )
        return None

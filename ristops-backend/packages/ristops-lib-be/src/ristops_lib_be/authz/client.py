from typing import Callable

from httpx import AsyncClient
from starlette.requests import Request

from ristops_lib_be.authz.interceptor import policy_to_grant
from ristops_lib_be.authz.policy import Policy
from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.schema.authz import ResourceType, ListUserResourceGrantsResponse, CheckAuthorizationRequest, AclCheckRequest


class CheckAuthorizationPolicy:
    """Asks the authz service whether a user satisfies a set of grants."""

    def __init__(self, authz_client_factory: Callable[[], AsyncClient]) -> None:
        self._authz_client_factory = authz_client_factory

    async def __call__(self, request: CheckAuthorizationRequest) -> bool:
        """Return whether the authz service authorizes the requested grants."""
        authz_client = self._authz_client_factory()
        _user = await authz_client.post(
            url=f"/users/{request.user_id}/acl-check",
            json=AclCheckRequest(grants=request.grants).model_dump(mode="json"),
        )
        return _user.json().get("is_authorized", False)


class AuthorizationResourceGrantsFetcher:
    """Dependency that fetches the resources of a type a user may access, to scope a search.

    Returns `None` when the user satisfies an override policy, signalling unrestricted access.
    """

    def __init__(
            self,
            authz_client_factory: Callable[[], AsyncClient],
            resource_type: ResourceType,
            *permissions: str,
            user_id: str | None = None,
            override_policies: tuple[Policy, ...] | None = None,
    ) -> None:
        self._authz_client_factory = authz_client_factory
        self._resource_type = resource_type
        self._permissions = permissions
        self._user_id = user_id
        self._override_policies = override_policies

    async def __call__(self, request: Request) -> ListUserResourceGrantsResponse | None:
        """Return the user's resource grants, or `None` for unrestricted access."""
        if self._user_id is None:
            user_id = APP_CONTEXT.get_or_throw(ContextKey.USER_ID)
        else:
            user_id = self._user_id
        should_override = await self._should_override(request)
        if should_override:
            return None
        authz_client = self._authz_client_factory()
        _response = await authz_client.get(
            f"/users/{user_id}/resources",
            params={
                "resource_type": self._resource_type,
                "permissions": self._permissions,
            },
        )
        return ListUserResourceGrantsResponse.model_validate_json(_response.content)

    async def _should_override(self, request: Request) -> bool:
        """Return whether the user satisfies any override policy (unrestricted access)."""
        if self._override_policies is None:
            return False
        grants = await policy_to_grant(request, self._override_policies)
        check_request = CheckAuthorizationRequest(
            user_id=APP_CONTEXT.get_or_throw(ContextKey.USER_ID),
            grants=grants,
        )
        check_policy_client = CheckAuthorizationPolicy(self._authz_client_factory)
        return await check_policy_client(check_request)

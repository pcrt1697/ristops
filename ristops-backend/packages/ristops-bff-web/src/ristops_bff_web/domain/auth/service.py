from datetime import datetime
from typing import Any
from uuid import UUID

from starlette.requests import Request

from ristops_bff_web.domain.auth.schema import UserCreationRequest
from ristops_bff_web.http import authn_client, authz_client
from ristops_bff_web.session import save_session
from ristops_lib_core.http import ResponseTransformer
from ristops_lib_core.schema.authn import LoginRequest, LoginResponse, RefreshTokenRequest

user_transformer = ResponseTransformer(
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
)

role_transformer = ResponseTransformer()

acl_transformer = ResponseTransformer(
    created_at=datetime.fromisoformat,
)

member_transformer = ResponseTransformer(
    created_at=datetime.fromisoformat,
)


async def login_user(login_request: LoginRequest, http_request: Request) -> dict[str, Any]:
    login_response = await _login(login_request, http_request)
    return await find_user(login_response.user_id)


async def _login(login_request: LoginRequest, http_request: Request) -> LoginResponse:
    payload = login_request.model_dump(mode="json")
    payload["password"] = login_request.password.get_secret_value()
    _login_response = await authn_client.client.post(
        url="auth/login",
        json=payload,
    )
    login_response = LoginResponse.model_validate_json(_login_response.content)
    await save_session(login_response, http_request)
    return login_response


async def find_user(user_id: str | UUID) -> dict[str, Any]:
    response = await authn_client.client.get(
        url=f"users/{user_id}",
    )
    return user_transformer.get_json(response)


async def find_me() -> dict[str, Any]:
    response = await authn_client.client.get(
        url=f"users/me",
    )
    return user_transformer.get_json(response)


async def register_user(creation_request: UserCreationRequest, http_request: Request) -> dict[str, Any]:
    payload = creation_request.model_dump(mode="json")
    payload["password"] = creation_request.password.get_secret_value()
    user_response = await authn_client.client.post(
        url="users",
        json=payload,
    )
    login_request = LoginRequest(
        email=creation_request.email,
        password=creation_request.password,
    )
    await _login(login_request, http_request)
    return user_transformer.get_json(user_response)


async def refresh_access_token(refresh_token: str, http_request: Request) -> LoginResponse:
    refresh_request = RefreshTokenRequest(
        refresh_token=refresh_token,
    )
    _refresh_response = await authn_client.client.post(
        url="auth/refresh",
        json=refresh_request.model_dump(mode="json"),
    )
    refresh_response = LoginResponse.model_validate_json(_refresh_response.content)
    await save_session(refresh_response, http_request)
    return refresh_response


async def update_user(user_id: str | UUID, update_user_input: dict[str, Any]) -> dict[str, Any]:
    response = await authn_client.client.patch(
        url=f"users/{user_id}",
        json=update_user_input,
    )
    return user_transformer.get_json(response)


async def find_role(role_id: str) -> dict[str, Any]:
    response = await authz_client.client.get(
        url=f"roles/{role_id}",
    )
    return role_transformer.get_json(response)


async def find_user_roles(user_id: str | UUID, list_grants_input: dict[str, Any]) -> dict[str, Any]:
    response = await authz_client.client.get(
        url=f"users/{user_id}/roles",
        params=list_grants_input,
    )
    return response.json()


async def list_roles(params: dict[str, Any]) -> list[dict[str, Any]]:
    response = await authz_client.client.get(
        url="roles",
        params=params,
    )
    return response.json()["roles"]


async def grant_access(grant_input: dict[str, Any]) -> dict[str, Any]:
    resource_type = grant_input["resource_type"]
    resource_id = grant_input["resource_id"]
    response = await authz_client.client.post(
        url=f"resources/{resource_type}/{resource_id}/acl",
        json={
            "user_id": grant_input["user_id"],
            "role_id": grant_input["role_id"],
        },
    )
    return acl_transformer.get_json(response)


async def revoke_access(revoke_input: dict[str, Any]) -> None:
    resource_type = revoke_input["resource_type"]
    resource_id = revoke_input["resource_id"]
    await authz_client.client.delete(
        url=f"resources/{resource_type}/{resource_id}/acl",
        params={
            "user_id": revoke_input["user_id"],
            "role_id": revoke_input["role_id"],
        },
    )


async def find_member(user_id: str | UUID) -> dict[str, Any]:
    response = await authn_client.client.get(
        url=f"members/{user_id}",
    )
    return member_transformer.get_json(response)


async def search_members(params: dict[str, Any]) -> dict[str, Any]:
    response = await authn_client.client.get(
        url="members",
        params=params,
    )
    page = response.json()
    page["items"] = [member_transformer.transform(item) for item in page["items"]]
    return page

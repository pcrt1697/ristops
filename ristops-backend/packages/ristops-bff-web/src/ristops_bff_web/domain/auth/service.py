from datetime import datetime
from typing import Any
from uuid import UUID

from starlette.requests import Request

from ristops_bff_web.domain.auth.schema import UserCreationRequest
from ristops_bff_web.http import http_service, HttpClient
from ristops_bff_web.session import save_session
from ristops_lib_core.http import ResponseTransformer
from ristops_lib_core.schema.authn import LoginRequest, LoginResponse, RefreshTokenRequest

user_transformer = ResponseTransformer(
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
)

role_transformer = ResponseTransformer()


async def login_user(login_request: LoginRequest, http_request: Request) -> dict[str, Any]:
    login_response = await _login(login_request, http_request)
    return await find_user(login_response.user_id)


async def _login(login_request: LoginRequest, http_request: Request) -> LoginResponse:
    payload = login_request.model_dump(mode="json")
    payload["password"] = login_request.password.get_secret_value()
    _login_response = await http_service.get(HttpClient.AUTHN).post(
        url="auth/login",
        json=payload,
    )
    login_response = LoginResponse.model_validate_json(_login_response.content)
    await save_session(login_response, http_request)
    return login_response


async def find_user(user_id: str | UUID) -> dict[str, Any]:
    response = await http_service.get(HttpClient.AUTHN).get(
        url=f"users/{user_id}",
    )
    return user_transformer.get_json(response)


async def find_me() -> dict[str, Any]:
    response = await http_service.get(HttpClient.AUTHN).get(
        url=f"users/me",
    )
    return user_transformer.get_json(response)


async def register_user(creation_request: UserCreationRequest, http_request: Request) -> dict[str, Any]:
    payload = creation_request.model_dump(mode="json")
    payload["password"] = creation_request.password.get_secret_value()
    user_response = await http_service.get(HttpClient.AUTHN).post(
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
    _refresh_response = await http_service.get(HttpClient.AUTHN).post(
        url="auth/refresh",
        json=refresh_request.model_dump(mode="json"),
    )
    refresh_response = LoginResponse.model_validate_json(_refresh_response.content)
    await save_session(refresh_response, http_request)
    return refresh_response


async def update_user(user_id: str | UUID, update_user_input: dict[str, Any]) -> dict[str, Any]:
    response = await http_service.get(HttpClient.AUTHN).patch(
        url=f"users/{user_id}",
        json=update_user_input,
    )
    return user_transformer.get_json(response)


async def find_role(role_id: str) -> dict[str, Any]:
    response = await http_service.get(HttpClient.AUTHZ).get(
        url=f"roles/{role_id}",
    )
    return role_transformer.get_json(response)


async def find_user_roles(user_id: str | UUID, list_roles_input: dict[str, Any]) -> dict[str, Any]:
    response = await http_service.get(HttpClient.AUTHZ).get(
        url=f"users/{user_id}/roles",
        params=list_roles_input,
    )
    return response.json()

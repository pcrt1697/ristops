from http import HTTPStatus

from fastapi import APIRouter
from starlette.requests import Request

from ristops_bff_web.domain.auth.service import login_user, register_user
from ristops_lib_core.auth.authn import public
from ristops_lib_core.schema.authn import LoginRequest
from ristops_bff_web.domain.auth.schema import UserCreationRequest
from ristops_lib_core.schema.user import UserResponse

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@auth_router.post(
    "/login",
    response_model=UserResponse,
)
@public
async def login(login_request: LoginRequest, http_request: Request) -> UserResponse:
    user = await login_user(login_request, http_request)
    return UserResponse.model_validate(user)


@auth_router.post(
    "/logout",
    status_code=HTTPStatus.NO_CONTENT,
)
async def logout(http_request: Request) -> None:
    http_request.session.clear()
    return None


@auth_router.post(
    "/register",
    status_code=HTTPStatus.CREATED,
)
@public
async def register(creation_request: UserCreationRequest, http_request: Request) -> UserResponse:
    user = await register_user(creation_request, http_request)
    return UserResponse.model_validate(user)

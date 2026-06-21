from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter
from fastapi.params import Path

from ristops_be_authn.domain.user.schema import UserCreationRequest, UserUpdateRequest
from ristops_be_authn.domain.user.service import (
    create_user, update_user, find_user_or_throw, find_me, remove_user, remove_me
)
from ristops_lib_be.authz.policy import policy, Policy, BaseResourceResolver
from ristops_lib_core.auth.authn import public
from ristops_lib_core.exception import ErrorResponse
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_core.schema.user import UserResponse
from ristops_lib_sql.engine import sql_transactional

_user_path_resolver = BaseResourceResolver(ResourceType.USER)

user_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@user_router.get(
    "/me",
    response_model=UserResponse
)
@policy()
@sql_transactional
async def get_me() -> UserResponse:
    """
    Returns the authenticated user.
    """

    user = await find_me()
    return UserResponse.model_validate(
        user,
        from_attributes=True,
        extra='ignore',
    )


@user_router.get(
    "/{user_id}",
    response_model=UserResponse
)
@policy(Policy(_user_path_resolver, "user~get"))
@sql_transactional
async def get(
        user_id: Annotated[UUID, Path(description="User ID")],
) -> UserResponse:
    user = await find_user_or_throw(user_id)
    return UserResponse.model_validate(
        user,
        from_attributes=True,
        extra='ignore',
    )


@user_router.post(
    "",
    response_model=UserResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Username or email already taken"},
    }
)
@public
@sql_transactional
async def create(request: UserCreationRequest) -> UserResponse:
    user = await create_user(request)
    return UserResponse.model_validate(
        user,
        from_attributes=True,
        extra='ignore',
    )


@user_router.patch(
    "/{user_id}",
    response_model=UserResponse
)
@policy(Policy(_user_path_resolver, "user~edit"))
@sql_transactional
async def update(
        user_id: Annotated[UUID, Path(description="User ID")],
        request: UserUpdateRequest,
) -> UserResponse:
    user = await update_user(user_id, request)
    return UserResponse.model_validate(
        user,
        from_attributes=True,
        extra='ignore',
    )


@user_router.delete(
    "/me",
    status_code=HTTPStatus.NO_CONTENT,
)
@policy()
@sql_transactional
async def delete_me(
) -> None:
    await remove_me()


@user_router.delete(
    "/{user_id}",
    status_code=HTTPStatus.NO_CONTENT,
)
@policy(Policy(_user_path_resolver, "user~remove"))
@sql_transactional
async def delete(
        user_id: Annotated[UUID, Path(description="User ID")],
) -> None:
    await remove_user(user_id)

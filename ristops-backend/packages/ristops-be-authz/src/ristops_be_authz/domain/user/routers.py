from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Path

from ristops_be_authz.database.engine import neo4j_transactional
from ristops_be_authz.domain.user.service import (
    create_user, remove_user, create_authenticate_user,
    remove_me
)
from ristops_lib_be.authz.policy import policy, Policy, BaseResourceResolver
from ristops_lib_core.auth.authn import public
from ristops_lib_core.schema.authz import (
    AuthorizationUserResponse, ResourceType
)

_user_path_resolver = BaseResourceResolver(ResourceType.USER)

user_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@user_router.post(
    "",
    response_model=AuthorizationUserResponse
)
@neo4j_transactional
async def create_me() -> AuthorizationUserResponse:
    """ Create the authenticated user. """
    user = await create_authenticate_user()
    return AuthorizationUserResponse(
        user_id=user.id,
    )


@user_router.post(
    "/{user_id}",
    response_model=AuthorizationUserResponse
)
@public
@neo4j_transactional
async def create(
        user_id: Annotated[str, Path(description="User ID")],
) -> AuthorizationUserResponse:
    """ Create the authenticated user. """
    user = await create_user(user_id)
    return AuthorizationUserResponse(
        user_id=user.id,
    )


@user_router.delete(
    "",
    status_code=HTTPStatus.NO_CONTENT,
)
@neo4j_transactional
async def delete_me() -> None:
    """ Delete the authenticated user. """
    await remove_me()


@user_router.delete(
    "/{user_id}",
    status_code=HTTPStatus.NO_CONTENT,
)
@policy(Policy(_user_path_resolver, "user~remove"))
@neo4j_transactional
async def delete(
        user_id: Annotated[str, Path(description="User ID")],
) -> None:
    """ Create the authenticated user. """
    await remove_user(user_id)

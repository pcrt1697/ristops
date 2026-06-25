from typing import Annotated

from fastapi import APIRouter, Path, Query

from ristops_be_authz.domain.acl.service import check_acl_authorization
from ristops_be_authz.domain.user.service import list_user_roles, list_user_resources
from ristops_lib_be.authz.policy import (
    policy, Policy, BaseResourceResolver, resolve_path_attribute
)
from ristops_lib_core.schema.authz import (
    ResourceType,
    ListUserGrantsResponse, ListUserResourceGrantsResponse,
    AclCheckRequest, CheckAuthorizationRequest, AuthorizationResponse,
)
from ristops_lib_neo4j.engine import neo4j_transactional

_user_path_resolver = BaseResourceResolver(ResourceType.USER, resolver=resolve_path_attribute)
user_router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@user_router.get(
    "/{user_id}/roles",
    response_model=ListUserGrantsResponse,
)
@policy(Policy(_user_path_resolver, "role~list"))
@neo4j_transactional
async def list_roles(
        user_id: Annotated[str, Path(description="User ID")],
        resource_id: Annotated[str, Query(description="Resource ID")],
        resource_type: Annotated[str, Query(description="Resource type")],
) -> ListUserGrantsResponse:
    """List unique permissions a user holds on a resource, including permissions inherited from ancestor resources."""
    grants = await list_user_roles(user_id, resource_type, resource_id)
    return ListUserGrantsResponse(grants=grants)


@user_router.get(
    "/{user_id}/resources",
    response_model=ListUserResourceGrantsResponse,
)
@policy(Policy(_user_path_resolver, "resource~list"))
@neo4j_transactional
async def list_resources(
        user_id: Annotated[str, Path(description="User ID")],
        resource_type: Annotated[ResourceType, Query(description="Resource type")],
        permissions: Annotated[list[str], Query(description="List of permissions")],
) -> ListUserResourceGrantsResponse:
    """List unique resources the user has grants, including grants inherited from ancestor resources."""
    grants = await list_user_resources(user_id, resource_type, permissions)
    return ListUserResourceGrantsResponse(grants=grants)


@user_router.post(
    "/{user_id}/acl-check",
    response_model=AuthorizationResponse,
)
@policy(Policy(_user_path_resolver, "acl~get"))
@neo4j_transactional
async def acl_check(
        user_id: Annotated[str, Path(description="User ID")],
        body: AclCheckRequest,
) -> AuthorizationResponse:
    """Evaluate whether the user satisfies the requested grants."""
    is_authorized = await check_acl_authorization(
        CheckAuthorizationRequest(user_id=user_id, grants=body.grants)
    )
    return AuthorizationResponse(is_authorized=is_authorized)

from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Path, Query

from ristops_be_authz.domain.acl.service import grant_access, revoke_access
from ristops_be_authz.domain.resource.schema import ResourceUserSearchQuery
from ristops_be_authz.domain.resource.service import search_resource_users
from ristops_lib_be.authz.policy import policy, Policy, resolve_path_resource
from ristops_lib_core.schema.authz import (
    ResourceType, AuthorizationResource, GrantAccessRequest, GrantRoleRequest,
    RevokeAccessRequest, AclResponse, ResourceUserGrantsResponse
)
from ristops_lib_core.schema.pagination import Page
from ristops_lib_neo4j.engine import neo4j_transactional

resource_router = APIRouter(
    prefix="/resources",
    tags=["resources"],
)


@resource_router.post(
    "/{resource_type}/{resource_id}/acl",
    response_model=AclResponse,
    status_code=HTTPStatus.CREATED,
)
@policy(Policy(resolve_path_resource, "acl~add"))
@neo4j_transactional
async def grant_resource_access(
        resource_type: Annotated[ResourceType, Path(description="Resource type")],
        resource_id: Annotated[str, Path(description="Resource identifier")],
        body: GrantRoleRequest,
) -> AclResponse:
    """Grant a role to a user on the resource."""
    request = GrantAccessRequest(
        user_id=body.user_id,
        role_id=body.role_id,
        resource=AuthorizationResource(
            resource_id=resource_id,
            resource_type=resource_type,
        ),
    )
    acl = await grant_access(request)
    return AclResponse(
        id=acl.id,
        created_at=acl.created_at,
        user_id=request.user_id,
        role_id=request.role_id,
        resource=request.resource,
    )


@resource_router.delete(
    "/{resource_type}/{resource_id}/acl",
    status_code=HTTPStatus.NO_CONTENT,
)
@policy(Policy(resolve_path_resource, "acl~remove"))
@neo4j_transactional
async def revoke_resource_access(
        resource_type: Annotated[ResourceType, Path(description="Resource type")],
        resource_id: Annotated[str, Path(description="Resource identifier")],
        user_id: Annotated[str, Query(description="ID of the user to revoke access from")],
        role_id: Annotated[str, Query(description="Role to revoke on the resource")],
) -> None:
    """Revoke a user's role on the resource."""
    request = RevokeAccessRequest(
        user_id=user_id,
        role_id=role_id,
        resource=AuthorizationResource(
            resource_id=resource_id,
            resource_type=resource_type,
        ),
    )
    await revoke_access(request)


@resource_router.get(
    "/{resource_type}/{resource_id}/users",
    response_model=Page[ResourceUserGrantsResponse],
)
@policy(Policy(resolve_path_resource, "acl~list"))
@neo4j_transactional
async def grant_resource_access(
        resource_type: Annotated[ResourceType, Path(description="Resource type")],
        resource_id: Annotated[str, Path(description="Resource identifier")],
        query: Annotated[ResourceUserSearchQuery, Query()],
) -> Page[ResourceUserGrantsResponse]:
    """Search users with granted access to the resource."""
    return await search_resource_users(resource_type, resource_id, query)

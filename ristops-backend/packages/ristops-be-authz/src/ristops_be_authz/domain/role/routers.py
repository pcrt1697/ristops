from typing import Annotated

from fastapi import APIRouter, Path

from ristops_be_authz.domain.role.service import find_role
from ristops_lib_be.authz.policy import policy, Policy, resolve_static_resource
from ristops_lib_core.schema.authz import RoleResponse, ResourceType
from ristops_lib_neo4j.engine import neo4j_transactional

roles_router = APIRouter(
    prefix="/roles",
    tags=["roles"],
)


@roles_router.get(
    "/{role_id}",
    response_model=RoleResponse,
)
@policy(Policy(resolve_static_resource("*", ResourceType.APP), "role~get"))
@neo4j_transactional
async def get_role(
        role_id: Annotated[str, Path(description="User ID")],
) -> RoleResponse:
    """Find a role by ID"""
    return await find_role(role_id)

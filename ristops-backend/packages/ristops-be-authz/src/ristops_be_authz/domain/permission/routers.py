from typing import Annotated

from fastapi import APIRouter, Query

from ristops_be_authz.domain.permission.service import list_permissions
from ristops_lib_be.authz.policy import policy, Policy, resolve_static_resource
from ristops_lib_core.schema.authz import (
    ResourceType, ListPermissionsResponse
)
from ristops_lib_neo4j.engine import neo4j_transactional

permissions_router = APIRouter(
    prefix="/permissions",
    tags=["permissions"],
)


@permissions_router.get(
    "",
    response_model=ListPermissionsResponse,
)
@policy(Policy(resolve_static_resource("*", ResourceType.APP), "permission:list"))
@neo4j_transactional
async def get_permissions(
        query: Annotated[
            str | None, Query(description="Permission query applied using `contains` operator")] = None,
) -> ListPermissionsResponse:
    """List permissions"""
    permissions = await list_permissions(query)
    return ListPermissionsResponse(permissions=permissions)

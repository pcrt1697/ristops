from http import HTTPStatus

from fastapi import HTTPException

from ristops_be_authz.domain.models import RoleNode
from ristops_lib_core.schema.authz import RoleResponse
from ristops_lib_neo4j.engine import get_neo4j_transaction


async def find_role_by_id(role_id: str) -> RoleNode | None:
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        "MATCH (r:Role {id: $id}) RETURN r",
        id=role_id,
    )
    record = await result.single()
    if record is None:
        return None
    return RoleNode.model_validate(record["r"])


async def find_role_by_id_or_throw(role_id: str) -> RoleNode:
    role = await find_role_by_id(role_id)
    if role is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Role not found.")
    return role


async def find_role(role_id: str) -> RoleResponse:
    """Find a role by ID with permissions attached to it."""
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        """
        MATCH (r:Role {id: $id})-[:GRANTS]->(p:Permission)
        RETURN r.id AS id,
               r.name AS name,
               r.description AS description,
               collect(DISTINCT p.id) AS permissions
        """,
        id=role_id,
    )
    record = await result.single()
    if record is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Role not found.")
    return RoleResponse(
        id=record["id"],
        name=record["name"],
        description=record["description"],
        permissions=record["permissions"],
    )

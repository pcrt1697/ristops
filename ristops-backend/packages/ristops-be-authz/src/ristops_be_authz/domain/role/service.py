from http import HTTPStatus

from fastapi import HTTPException

from ristops_be_authz.database.engine import get_neo4j_transaction
from ristops_be_authz.domain.models import RoleNode


async def get_role_by_id(role_id: str) -> RoleNode | None:
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        "MATCH (r:Role {id: $id}) RETURN r",
        id=role_id,
    )
    record = await result.single()
    if record is None:
        return None
    return RoleNode.model_validate(record["r"])


async def get_role_by_id_or_throw(role_id: str) -> RoleNode:
    role = await get_role_by_id(role_id)
    if role is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Role not found.")
    return role

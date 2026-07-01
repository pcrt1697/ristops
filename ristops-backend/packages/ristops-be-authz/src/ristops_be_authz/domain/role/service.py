from http import HTTPStatus

from fastapi import HTTPException

from ristops_be_authz.domain.models import RoleNode
from ristops_lib_core.schema.authz import RoleResponse, ListRolesQuery, PERMISSION_SEPARATOR
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
               r.scope AS scope,
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
        scope=record["scope"],
        permissions=record["permissions"],
    )


async def list_roles(query: ListRolesQuery) -> list[RoleResponse]:
    transaction = get_neo4j_transaction()
    permission = query.permission.lower() if query.permission else None
    # When the filter is a full permission id (e.g. "venue:add"), also match roles granting the
    # scope wildcard ("venue:*"); the global wildcard ("*") is matched in the query unconditionally.
    permission_scope_wildcard = None
    if permission and PERMISSION_SEPARATOR in permission:
        scope = permission.split(PERMISSION_SEPARATOR)[0]
        permission_scope_wildcard = f"{scope}{PERMISSION_SEPARATOR}*"
    result = await transaction.run(
        """
        MATCH (r:Role)
        WHERE ($role_id IS NULL OR toLower(r.id) CONTAINS $role_id)
          AND ($role_name IS NULL OR toLower(r.name) CONTAINS $role_name)
          AND ($scope IS NULL OR r.scope = $scope)
          AND ($permission IS NULL OR EXISTS {
                MATCH (r)-[:GRANTS]->(p:Permission)
                WHERE toLower(p.id) CONTAINS $permission
                   OR p.id = '*'
                   OR ($permission_scope_wildcard IS NOT NULL AND toLower(p.id) = $permission_scope_wildcard)
          })
        OPTIONAL MATCH (r)-[:GRANTS]->(perm:Permission)
        RETURN r.id          AS id,
               r.name        AS name,
               r.description AS description,
               r.scope       AS scope,
               collect(DISTINCT perm.id) AS permissions
        ORDER BY r.name
        """,
        role_id=query.role_id.lower() if query.role_id else None,
        role_name=query.role_name.lower() if query.role_name else None,
        scope=query.scope.value if query.scope else None,
        permission=permission,
        permission_scope_wildcard=permission_scope_wildcard,
    )
    return [RoleResponse(**record.data()) async for record in result]

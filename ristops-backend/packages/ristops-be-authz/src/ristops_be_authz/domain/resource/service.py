import logging
from http import HTTPStatus

from fastapi import HTTPException
from neo4j import Record

from ristops_be_authz.domain.models import ResourceNode
from ristops_be_authz.domain.resource.schema import ResourceUserSearchQuery
from ristops_lib_be.authz.events import (
    resource_lifecycle_event_adapter, ResourceCreatedLifecycleEvent,
    ResourceDeletedLifecycleEvent
)
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_core.schema.authz import (
    ResourceType, AuthorizationResource, ResourceUserGrantsResponse, PERMISSION_SEPARATOR
)
from ristops_lib_core.schema.pagination import Page, SortDirection
from ristops_lib_neo4j.engine import get_neo4j_transaction, neo4j_transaction_provider
from ristops_lib_redis.engine import StreamPayload

_logger = logging.getLogger(__name__)


async def find_resource_or_throw(resource_type: str, resource_id: str) -> ResourceNode:
    """Fetch a resource node or raise 404."""
    record = await _find_resource(resource_type, resource_id)
    if record is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Resource not found")
    return ResourceNode.model_validate(record["r"])


async def find_or_create_user_resource(user_id: str) -> None:
    _logger.info("Creating user resource for %s", user_id)
    resources = [
        AuthorizationResource(
            resource_id=user_id,
            resource_type=ResourceType.USER,
        )
    ]
    await find_or_create_resources(
        parent_type=ResourceType.APP,
        parent_id="*",
        resources=resources,
    )


async def find_or_create_resources(
        parent_type: ResourceType,
        parent_id: str,
        resources: list[AuthorizationResource],
) -> list[ResourceNode]:
    _logger.info("Creating %s resources", len(resources))
    await find_resource_or_throw(parent_type, parent_id)
    transaction = get_neo4j_transaction()
    nodes = []
    for resource in resources:
        result = await transaction.run(
            """
            MATCH (p:Resource {resource_type: $parent_type, resource_id: $parent_id})
            MERGE (c:Resource {resource_type: $resource_type, resource_id: $resource_id})
            MERGE (c)-[:BELONGS_TO]->(p)
            RETURN c
            """,
            parent_type=parent_type.value,
            parent_id=parent_id,
            resource_type=resource.resource_type.value,
            resource_id=resource.resource_id,
        )
        record = await result.single()
        if record is None:
            raise RuntimeError("Failed to create resource")
        node = ResourceNode.model_validate(record["c"])
        _logger.info("Created resource %s/%s", node.resource_type, node.resource_id)
        nodes.append(node)
    return nodes


async def find_or_create_root() -> ResourceNode:
    _logger.info(f"Creating root resource...")
    return await _find_or_create_resource(ResourceType.APP.value, "*")


async def _find_or_create_resource(
        resource_type: str,
        resource_id: str,
) -> ResourceNode:
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        """
        MERGE (r:Resource {resource_type: $resource_type, resource_id: $resource_id})
        RETURN r
        """,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    record = await result.single()
    if record is None:
        raise RuntimeError("Failed to get or create resource")
    node = ResourceNode.model_validate(record["r"])
    _logger.info("Created resource %s/%s", node.resource_type, node.resource_id)
    return node


async def _find_resource(
        resource_type: str,
        resource_id: str,
) -> Record | None:
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        """
        MATCH (r:Resource {resource_type: $resource_type, resource_id: $resource_id})
        RETURN r
        LIMIT 1
        """,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    return await result.single()


async def resource_exists(resource_type: str, resource_id: str) -> bool:
    record = await _find_resource(resource_type, resource_id)
    return record is not None


async def throw_if_resource_not_exists(resource_type: str, resource_id: str) -> None:
    if not await resource_exists(resource_type, resource_id):
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Resource not found")


async def delete_resource(resource_type: ResourceType, resource_id: str) -> None:
    transaction = get_neo4j_transaction()
    await transaction.run(
        """
        MATCH (r:Resource {resource_type: $resource_type, resource_id: $resource_id})
        DETACH DELETE r
        """,
        resource_type=resource_type.value,
        resource_id=resource_id,
    )
    _logger.info("Deleted resource %s/%s", resource_type.value, resource_id)


async def on_resource_event(_: str, payload: StreamPayload) -> None:
    event = resource_lifecycle_event_adapter.validate_json(payload)
    async with neo4j_transaction_provider.context():
        if event.operation == LifecycleOperationType.CREATED:
            _event: ResourceCreatedLifecycleEvent = event
            await find_or_create_resources(_event.parent_type, _event.parent_id, _event.resources)
        elif event.operation == LifecycleOperationType.DELETED:
            _event: ResourceDeletedLifecycleEvent = event
            await delete_resource(_event.resource_type, _event.resource_id)


# Sortable fields -> the Cypher expression they map to (whitelisted via ResourceUserSortField,
# so interpolating them into ORDER BY is safe).
_RESOURCE_USER_SORT_EXPR = {
    "id": "u.id",
    "username": "u.username",
    "display_name": "u.display_name",
}

# Candidate users + filters: a user qualifies if they hold at least one role on the resource
# OR any of its ancestors (direct or inherited), matching the optional role-level filters.
# Username/display_name are stored lowercased, so we compare against lowercased params (index-friendly);
# role/permission ids are compared case-insensitively via toLower().
_RESOURCE_USERS_BASE = """
MATCH (target:Resource {resource_type: $resource_type, resource_id: $resource_id})
MATCH (target)-[:BELONGS_TO*0..]->(:Resource)<-[:ON]-(:Acl)<-[:HAS_ACCESS]-(u:User)
WITH DISTINCT target, u
WHERE ($username IS NULL OR u.username CONTAINS $username)
  AND ($display_name IS NULL OR u.display_name CONTAINS $display_name)
  AND EXISTS {
    MATCH (u)-[:HAS_ACCESS]->(acl:Acl)-[:ON]->(src:Resource)
    WHERE (target)-[:BELONGS_TO*0..]->(src)
    MATCH (acl)-[:WITH_ROLE]->(role:Role)
    WHERE ($role_id IS NULL OR toLower(role.id) CONTAINS $role_id)
      AND ($role_name IS NULL OR toLower(role.name) CONTAINS $role_name)
      AND ($permission IS NULL OR EXISTS {
            MATCH (role)-[:GRANTS]->(p:Permission)
            WHERE toLower(p.id) CONTAINS $permission
               OR p.id = '*'
               OR ($permission_scope_wildcard IS NOT NULL AND toLower(p.id) = $permission_scope_wildcard)
      })
  }
"""

_RESOURCE_USERS_COUNT = _RESOURCE_USERS_BASE + "\nRETURN count(u) AS total"

# for each matching user, return ALL their grants on the scope (not just the ones matching the
# filter) so the caller sees the full picture, with each grant's source resource
# (to identify non-direct, inherited, grants)
_RESOURCE_USERS_PAGE = _RESOURCE_USERS_BASE + """
CALL (u, target) {
    MATCH (u)-[:HAS_ACCESS]->(acl:Acl)-[:ON]->(src:Resource)
    WHERE (target)-[:BELONGS_TO*0..]->(src)
    MATCH (acl)-[:WITH_ROLE]->(role:Role)
    RETURN
        collect({
            resource: {resource_id: src.resource_id, resource_type: src.resource_type},
            role_id: role.id,
            assigned_at: acl.created_at
        }) AS grants
}
WITH u, grants
ORDER BY __ORDER_BY__
SKIP $skip
LIMIT $limit
RETURN u.id AS user_id, grants
"""


def _build_resource_users_order_by(query: ResourceUserSearchQuery) -> str:
    """Build the ORDER BY clause from the validated sort clauses (fields are enum-whitelisted)."""
    parts = []
    for clause in query.get_sort_clauses():
        expression = _RESOURCE_USER_SORT_EXPR.get(clause.field)
        if expression is None:
            continue
        direction = "DESC" if clause.direction == SortDirection.DESC else "ASC"
        parts.append(f"{expression} {direction}")
    return ", ".join(parts) if parts else "u.username ASC"


async def search_resource_users(
        resource_type: ResourceType,
        resource_id: str,
        query: ResourceUserSearchQuery
) -> Page[ResourceUserGrantsResponse]:
    """Page of users with access to the resource, each with their (direct + inherited) role grants."""
    transaction = get_neo4j_transaction()
    permission = query.permission.lower() if query.permission else None
    # When the filter is a full permission id (e.g. "venue:add"), also match roles granting the
    # scope wildcard ("venue:*"); the global wildcard ("*") is matched in the query unconditionally.
    permission_scope_wildcard = None
    if permission and PERMISSION_SEPARATOR in permission:
        scope = permission.split(PERMISSION_SEPARATOR)[0]
        permission_scope_wildcard = f"{scope}{PERMISSION_SEPARATOR}*"
    params = {
        "resource_type": resource_type.value,
        "resource_id": resource_id,
        "username": query.username.lower() if query.username else None,
        "display_name": query.display_name.lower() if query.display_name else None,
        "role_id": query.role_id.lower() if query.role_id else None,
        "role_name": query.role_name.lower() if query.role_name else None,
        "permission": permission,
        "permission_scope_wildcard": permission_scope_wildcard,
        "skip": query.page * query.page_size,
        "limit": query.page_size,
    }

    count_result = await transaction.run(_RESOURCE_USERS_COUNT, params)
    count_record = await count_result.single()
    total = count_record["total"] if count_record is not None else 0

    page_query = _RESOURCE_USERS_PAGE.replace("__ORDER_BY__", _build_resource_users_order_by(query))
    page_result = await transaction.run(page_query, params)
    items = [
        ResourceUserGrantsResponse.model_validate({
            "user_id": record["user_id"],
            "grants": record["grants"],
        })
        async for record in page_result
    ]
    return Page.create(items=items, total=total, params=query)

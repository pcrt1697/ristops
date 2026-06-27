import logging
from datetime import datetime, UTC
from http import HTTPStatus

from fastapi import HTTPException

from ristops_be_authz.domain.acl.service import create_member_acl
from ristops_be_authz.domain.models import UserNode
from ristops_be_authz.domain.resource.service import (
    find_or_create_user_resource, delete_resource, find_resource_or_throw,
)
from ristops_lib_be.authz.events import UserLifecycleEvent
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_core.schema.authz import (
    ResourceType, PermissionGrant, AuthorizationResource, ResourceGrant,
    RolePermissions
)
from ristops_lib_core.schema.user import AppMember
from ristops_lib_neo4j.engine import get_neo4j_transaction, neo4j_transaction_provider
from ristops_lib_redis.engine import StreamPayload

_logger = logging.getLogger(__name__)


async def find_user_by_id(user_id: str) -> UserNode | None:
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        "MATCH (u:User {id: $id}) RETURN u",
        id=user_id,
    )
    record = await result.single()
    if record is None:
        return None
    return UserNode.model_validate(record["u"])


async def upsert_user(info: AppMember) -> UserNode:
    """Create or update the local user read-model. Idempotent: handles both create and update events.

    Replicates the user's display fields (username, display_name) from be-authn and ensures the
    user's own resource and base member ACL exist. Re-running with the same payload is a no-op.
    """
    user_id = str(info.id)
    transaction = get_neo4j_transaction()
    await transaction.run(
        """
        MERGE (u:User {id: $id})
          ON CREATE SET u.created_at = $created_at
        SET u.username = $username,
            u.display_name = $display_name
        """,
        id=user_id,
        # stored lowercased: these are a search-only index (never returned/displayed —
        # the frontend reads member info from be-authn), so the TEXT indexes back
        # case-insensitive CONTAINS by lowercasing the search term at query time.
        username=info.username.lower(),
        display_name=info.display_name.lower() if info.display_name else None,
        created_at=datetime.now(UTC).isoformat(),
    )
    # both are idempotent (MERGE-based), so they self-heal on update too
    await find_or_create_user_resource(user_id)
    await create_member_acl(user_id)
    user = await find_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to upsert user")
    return user


async def remove_user(user_id: str) -> None:
    await delete_resource(ResourceType.USER, user_id)
    transaction = get_neo4j_transaction()
    await transaction.run(
        """
        MATCH (u:User {id: $id})
        DETACH DELETE u
        """,
        id=user_id,
    )
    _logger.info(f"Deleted user {user_id}")


async def list_user_roles(user_id: str, resource_type: str, resource_id: str) -> list[PermissionGrant]:
    """Return all permissions the user holds on the resource, including those inherited from ancestor resources."""
    await find_resource_or_throw(resource_type, resource_id)

    transaction = get_neo4j_transaction()
    result = await transaction.run(
        """
        MATCH (u:User {id: $user_id})-[:HAS_ACCESS]->(acl:Acl)-[:ON]->(r:Resource)
        WHERE (r.resource_type = $resource_type AND r.resource_id = $resource_id)
           OR EXISTS { MATCH (r)<-[:BELONGS_TO*]-(target:Resource {resource_type: $resource_type, resource_id: $resource_id}) }
        MATCH (acl)-[:WITH_ROLE]->(role:Role)
        RETURN role.id AS role_id,
               r.resource_type AS resource_type,
               r.resource_id AS resource_id
        """,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    records = await result.data()
    return [
        PermissionGrant(
            role_id=row["role_id"],
            resource=AuthorizationResource(
                resource_type=row["resource_type"],
                resource_id=row["resource_id"],
            ),
        )
        for row in records
    ]


async def list_user_resources(user_id: str, resource_type: ResourceType, permissions: list[str]) -> list[ResourceGrant]:
    """List all resources the user has grants, including grants inherited from ancestor resources."""
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        """
        MATCH (u:User {id: $user_id})-[:HAS_ACCESS]->(acl:Acl)-[:ON]->(r:Resource)
        MATCH (target:Resource {resource_type: $resource_type})-[:BELONGS_TO*0..]->(r)
        MATCH (acl)-[:WITH_ROLE]->(role:Role)-[:GRANTS]->(p:Permission)
        WHERE p.id IN $permissions
        WITH target, role, collect(DISTINCT p.id) AS role_permissions
        RETURN target.resource_type AS resource_type,
               target.resource_id   AS resource_id,
               collect({role_id: role.id, permissions: role_permissions}) AS roles
        """,
        user_id=user_id,
        resource_type=resource_type,
        permissions=permissions,
    )
    records = await result.data()
    return [
        ResourceGrant(
            resource=AuthorizationResource(
                resource_type=row["resource_type"],
                resource_id=row["resource_id"],
            ),
            roles=[
                RolePermissions(
                    role_id=role["role_id"],
                    permissions=role["permissions"],
                )
                for role in row["roles"]
            ],
        )
        for row in records
    ]


async def on_user_event(_: str, payload: StreamPayload) -> None:
    event = UserLifecycleEvent.model_validate(payload)
    async with neo4j_transaction_provider.context():
        if event.operation in (LifecycleOperationType.CREATED, LifecycleOperationType.UPDATED):
            await upsert_user(event)
        elif event.operation == LifecycleOperationType.DELETED:
            await remove_user(str(event.id))

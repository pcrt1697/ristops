import logging
from datetime import datetime, UTC
from http import HTTPStatus
from uuid import uuid5, UUID

from fastapi import HTTPException

from ristops_be_authz.domain.models import AclNode
from ristops_be_authz.domain.resource.service import (
    find_or_create_root, throw_if_resource_not_exists
)
from ristops_be_authz.domain.role.service import find_role_by_id_or_throw
from ristops_lib_core.auth.authn import RISTOPS_NAMESPACE_UUID, DEFAULT_ADMIN_USERNAME
from ristops_lib_core.schema.authz import (
    RevokeAccessRequest, CheckAuthorizationRequest,
    ResourceType, AuthorizationResource, PERMISSION_SEPARATOR
)
from ristops_lib_neo4j.engine import get_neo4j_transaction, neo4j_transactional

_logger = logging.getLogger(__name__)
_SYSTEM_ADMIN_ROLE = "admin"
_SYSTEM_MEMBER_ROLE = "member"


def _scope_wildcard(permission: str) -> str:
    """Return the scope wildcard for a permission (e.g. "venue:add" -> "venue:*")."""
    scope = permission.split(PERMISSION_SEPARATOR)[0]
    return f"{scope}{PERMISSION_SEPARATOR}*"


def get_acl_id(user_id: str, resource_type: ResourceType, resource_id: str, role_id: str) -> str:
    _acl_id = uuid5(
        RISTOPS_NAMESPACE_UUID,
        f"{user_id}|{resource_type.value}|{resource_id}|{role_id}",
    )
    return str(_acl_id)


async def grant_access(
        user_id: str,
        role_id: str,
        resource: AuthorizationResource,
        expires_at: datetime | None = None,
) -> AclNode:
    """ Grant the user access to the resource with the given role. Idempotent per (user, resource, role). """

    await throw_if_resource_not_exists(resource.resource_type.value, resource.resource_id)
    role = await find_role_by_id_or_throw(role_id)

    # A role can only be assigned to resources of its declared scope.
    if resource.resource_type.value != role.scope:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Role '{role.id}' cannot be assigned to a '{resource.resource_type.value}' resource",
        )

    transaction = get_neo4j_transaction()
    # deterministic id from the (user, resource, role) tuple: the acl_id UNIQUE constraint then
    # enforces a single ACL per tuple and makes the grant idempotent.
    acl_id = get_acl_id(
        user_id=user_id,
        resource_type=resource.resource_type,
        resource_id=resource.resource_id,
        role_id=role.id,
    )

    _logger.info(f"Creating ACL entry {acl_id}")
    # expires_at is set on every grant (not only ON CREATE) so re-granting updates the expiry.
    result = await transaction.run(
        """
        MATCH (role:Role {id: $role_id})
        MATCH (r:Resource {resource_type: $resource_type, resource_id: $resource_id})
        MATCH (u:User {id: $user_id})
        MERGE (acl:Acl {id: $acl_id})
          ON CREATE SET acl.created_at = $created_at
        SET acl.expires_at = $expires_at
        MERGE (u)-[:HAS_ACCESS]->(acl)
        MERGE (acl)-[:ON]->(r)
        MERGE (acl)-[:WITH_ROLE]->(role)
        RETURN acl
        """,
        role_id=role.id,
        user_id=user_id,
        resource_type=resource.resource_type.value,
        resource_id=resource.resource_id,
        acl_id=acl_id,
        created_at=datetime.now(UTC).isoformat(),
        expires_at=expires_at.isoformat() if expires_at else None,
    )
    record = await result.single()
    if record is None:
        # role and resource are validated above, so an empty result means the user
        # node doesn't exist (not yet replicated from be-authn).
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="User not found",
        )
    node = AclNode.model_validate(record["acl"])
    _logger.info(f"Created ACL entry {node.id}")
    return node


async def revoke_access(request: RevokeAccessRequest) -> None:
    """Revoke a user's role grant on a resource by deleting the matching ACL entry."""
    acl_id = get_acl_id(
        user_id=request.user_id,
        resource_type=request.resource.resource_type,
        resource_id=request.resource.resource_id,
        role_id=request.role_id,
    )
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        """
        MATCH (acl:Acl {id: $acl_id})
        DETACH DELETE acl
        """,
        {"acl_id": acl_id},
    )
    summary = await result.consume()
    if summary.counters.nodes_deleted == 0:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail="ACL entry not found",
        )


async def create_member_acl(user_id: str) -> None:
    await grant_access(
        user_id=user_id,
        role_id=_SYSTEM_MEMBER_ROLE,
        resource=AuthorizationResource(
            resource_id=user_id,
            resource_type=ResourceType.USER,
        ),
    )


async def delete_user_acl(user_id: str) -> None:
    """ Delete all user ACL. """
    transaction = get_neo4j_transaction()
    await transaction.run(
        """
        MATCH (u:User {id: $user_id})-[:HAS_ACCESS]->(acl:Acl)
        DETACH DELETE acl
        """,
        {"user_id": user_id},
    )
    _logger.info(f"Deleted ACL for user {user_id}")


async def initialize_acl_seed() -> UUID:
    """ Clear admin ACL and upsert root resource. """
    admin_id = uuid5(RISTOPS_NAMESPACE_UUID, DEFAULT_ADMIN_USERNAME)
    await delete_user_acl(str(admin_id))
    await find_or_create_root()
    return admin_id


async def assign_admin_role(admin_id: UUID) -> None:
    """ Create ACL for admin user. """
    acl = await grant_access(
        user_id=str(admin_id),
        role_id=_SYSTEM_ADMIN_ROLE,
        resource=AuthorizationResource(
            resource_id="*",
            resource_type=ResourceType.APP,
        ),
    )
    _logger.info(f"ACL setup completed for admin, created entry {acl.id}")


@neo4j_transactional
async def check_acl_authorization(request: CheckAuthorizationRequest) -> bool:
    """ Returns true if the user is allowed to perform the requested actions. """

    # flatten all grants into a list of individual permission checks
    # each check contains the resource id and the permission to verify
    checks = [
        {
            "resource_type": grant.resource.resource_type.value,
            "resource_id": grant.resource.resource_id,
            "permission": permission,
            "scope_wildcard": _scope_wildcard(permission),  # e.g. "order:*" from "order:listItems"
        }
        for grant in request.grants
        for permission in grant.permissions
    ]
    transaction = get_neo4j_transaction()
    _result = await transaction.run(
        """
        // iterate over each permission check
        UNWIND $checks AS check

        // find acl entries for the user on the target resource
        // or any ancestor resource in the hierarchy (BELONGS_TO*), excluding expired grants
        MATCH (u:User {id: $user_id})-[:HAS_ACCESS]->(acl:Acl)-[:ON]->(r:Resource)
        WHERE (acl.expires_at IS NULL OR datetime(acl.expires_at) > datetime($now))
          AND (
            (r.resource_type = check.resource_type AND r.resource_id = check.resource_id)
            OR EXISTS {
                MATCH (r)<-[:BELONGS_TO*]-(target:Resource {resource_type: check.resource_type, resource_id: check.resource_id})
            }
          )

        // follow the acl to the role and check if the role grants the permission
        // supports exact match, scope wildcard (e.g. orderItem:*) and full wildcard (*)
        MATCH (acl)-[:WITH_ROLE]->(:Role)-[:GRANTS]->(p:Permission)
        WHERE p.id = check.permission
           OR p.id = check.scope_wildcard
           OR p.id = '*'

        // aggregate results — true only if every single check passed
        WITH check, count(p) > 0 AS allowed
        RETURN all(allowed IN collect(allowed) WHERE allowed = true)
        """,
        {
            "user_id": str(request.user_id),
            "checks": checks,
            "now": datetime.now(UTC).isoformat(),
        },
    )
    result = await _result.single()
    # no results -> deny access
    if result is None:
        return False
    return bool(result.value(default=False))

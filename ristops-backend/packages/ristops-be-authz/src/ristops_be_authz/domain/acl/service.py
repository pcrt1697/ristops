import logging
from datetime import datetime, UTC
from uuid import uuid5, uuid4

from ristops_be_authz.domain.models import AclNode
from ristops_be_authz.domain.resource.service import (
    make_resource_id, find_or_create_root, throw_if_resource_not_exists
)
from ristops_be_authz.domain.role.service import get_role_by_id_or_throw
from ristops_lib_core.auth.authn import RISTOPS_NAMESPACE_UUID, DEFAULT_ADMIN_USERNAME
from ristops_lib_core.schema.authz import GrantAccessRequest, CheckAuthorizationRequest, ResourceType
from ristops_lib_neo4j.engine import get_neo4j_transaction, neo4j_transactional

_logger = logging.getLogger(__name__)
_SYSTEM_ADMIN_ROLE = "admin"
_SYSTEM_MEMBER_ROLE = "member"


async def grant_access(request: GrantAccessRequest) -> AclNode:
    """ Grants the user to access resource. If the ACL entry already exists, then it is not created. """

    _resource_exists = await throw_if_resource_not_exists(request.resource_type.value, request.resource_id)
    role = await get_role_by_id_or_throw(request.role_id)

    transaction = get_neo4j_transaction()
    _resource_id = make_resource_id(request.resource_type, request.resource_id)
    _acl_id = uuid4()

    _logger.info(f"Creating ACL entry {_acl_id}")
    result = await transaction.run(
        """
        MATCH (role:Role {id: $role_id})
        MATCH (r:Resource {id: $resource_id})
        MERGE (u:User {id: $user_id})
        ON CREATE SET u.id = $user_id, u.created_at = $created_at
        MERGE (u)-[:HAS_ACCESS]->(acl:Acl)-[:ON]->(r)
        MERGE (acl)-[:WITH_ROLE]->(role)
        ON CREATE SET acl.id = $acl_id, acl.created_at = $created_at
        RETURN acl
        """,
        role_id=role.id,
        user_id=request.user_id,
        resource_id=_resource_id,
        acl_id=str(_acl_id),
        created_at=datetime.now(UTC).isoformat(),
    )
    record = await result.single()
    if record is None:
        raise RuntimeError("Failed to create ACL entry")
    node = AclNode.model_validate(record["acl"])
    _logger.info(f"Created ACL entry {node.id}")
    return node


async def create_member_acl(user_id: str) -> None:
    request = GrantAccessRequest(
        user_id=user_id,
        role_id=_SYSTEM_MEMBER_ROLE,
        resource_id=user_id,
        resource_type=ResourceType.USER,
    )
    await grant_access(request)


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


@neo4j_transactional
async def setup_admin_acl() -> None:
    """ Create ACL for admin user. """

    admin_id = str(uuid5(RISTOPS_NAMESPACE_UUID, DEFAULT_ADMIN_USERNAME))
    _logger.info(f"Setting up ACL for admin {admin_id}")

    await delete_user_acl(admin_id)
    request = GrantAccessRequest(
        user_id=admin_id,
        role_id=_SYSTEM_ADMIN_ROLE,
        resource_id="*",
        resource_type=ResourceType.APP,
    )
    _logger.info(f"Creating root resource...")
    await find_or_create_root()
    acl = await grant_access(request)
    _logger.info(f"ACL setup completed for admin, created entry {acl.id}")


@neo4j_transactional
async def check_acl_authorization(request: CheckAuthorizationRequest) -> bool:
    """ Returns true if the user is allowed to perform the requested actions. """

    # flatten all grants into a list of individual permission checks
    # each check contains the resource id and the permission to verify
    checks = [
        {
            "resource_id": make_resource_id(
                grant.resource.resource_type,
                grant.resource.resource_id,
            ),
            "permission": permission,
            "scope": permission.split("~")[0],  # e.g. "order" from "order~listItems"
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
        // or any ancestor resource in the hierarchy (BELONGS_TO*)
        MATCH (u:User {id: $user_id})-[:HAS_ACCESS]->(acl:Acl)-[:ON]->(r:Resource)
        WHERE r.id = check.resource_id
            OR EXISTS {
                MATCH (r)<-[:BELONGS_TO*]-(target:Resource {id: check.resource_id})
            }

        // follow the acl to the role and check if the role grants the permission
        // supports exact match, scope wildcard (e.g. orderItem.*) and full wildcard (*)
        MATCH (acl)-[:WITH_ROLE]->(:Role)-[:GRANTS]->(p:Permission)
        WHERE p.id = check.permission
           OR p.id = check.scope + '~*'
           OR p.id = '*'

        // aggregate results — true only if every single check passed
        WITH check, count(p) > 0 AS allowed
        RETURN all(allowed IN collect(allowed) WHERE allowed = true)
        """,
        {
            "user_id": str(request.user_id),
            "checks": checks,
        },
    )
    result = await _result.single()
    # no results -> deny access
    if result is None:
        return False
    return bool(result.value(default=False))

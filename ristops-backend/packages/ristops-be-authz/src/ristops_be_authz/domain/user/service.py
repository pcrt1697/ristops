import logging
from http import HTTPStatus

from fastapi import HTTPException

from ristops_be_authz.domain.acl.service import create_member_acl
from ristops_be_authz.domain.models import UserNode
from ristops_be_authz.domain.resource.service import find_or_create_user_resource, delete_resource
from ristops_lib_be.authz.events import AuthZUserEvent
from ristops_lib_be.events import ResourceEventType
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_neo4j.engine import get_neo4j_transaction, neo4j_transaction_provider
from ristops_lib_redis.engine import StreamPayload

_logger = logging.getLogger(__name__)


async def get_user_by_id(user_id: str) -> UserNode | None:
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        "MATCH (u:User {id: $id}) RETURN u",
        id=user_id,
    )
    record = await result.single()
    if record is None:
        return None
    return UserNode.model_validate(record["u"])


async def create_user(user_id: str) -> UserNode:
    await find_or_create_user_resource(user_id)
    await create_member_acl(user_id)
    user = await get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to create user")
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


async def on_user_event(_: str, payload: StreamPayload) -> None:
    event = AuthZUserEvent.model_validate(payload)
    async with neo4j_transaction_provider.context():
        if event.operation == ResourceEventType.CREATED:
            await create_user(event.user_id)
        elif event.operation == ResourceEventType.DELETED:
            await remove_user(event.user_id)

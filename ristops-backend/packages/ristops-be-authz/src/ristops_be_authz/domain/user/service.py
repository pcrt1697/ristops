import logging
from http import HTTPStatus

from fastapi import HTTPException
from redis.typing import EncodableT

from ristops_be_authz.database.engine import get_neo4j_transaction, neo4j_transaction_provider
from ristops_be_authz.domain.acl.service import create_member_acl
from ristops_be_authz.domain.models import UserNode
from ristops_be_authz.domain.resource.service import find_or_create_user_resource
from ristops_lib_be.authz.events import AuthZUserEvent
from ristops_lib_be.events import ResourceEventType
from ristops_lib_core.context import APP_CONTEXT, ContextKey

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


async def create_authenticate_user() -> UserNode:
    user_id = APP_CONTEXT.get_or_throw(ContextKey.USER_ID)
    return await create_user(user_id)


async def create_user(user_id: str) -> UserNode:
    await find_or_create_user_resource(user_id)
    await create_member_acl(user_id)
    user = await get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to create user")
    return user


async def remove_me() -> None:
    user_id = APP_CONTEXT.get_or_throw(ContextKey.USER_ID)
    return await remove_user(user_id)


async def remove_user(user_id: str) -> None:
    transaction = get_neo4j_transaction()
    await transaction.run(
        """
        MATCH (u:User {id: $id})
        DETACH DELETE u
        """,
        id=user_id,
    )
    _logger.info(f"Deleted user {user_id}")


async def on_user_event(stream_id: str, payload: EncodableT) -> None:
    async with neo4j_transaction_provider.context():
        event = AuthZUserEvent.model_validate(payload)
        if event.operation == ResourceEventType.created:
            await create_user(event.user_id)
        else:
            await remove_user(event.user_id)

import logging
from uuid import UUID

from ristops_be_authn.services.http import http_service, HttpClient
from ristops_be_authn.settings import UserProducerSettings
from ristops_lib_be.authz.events import AuthZUserEvent
from ristops_lib_be.events import ResourceEventType
from ristops_lib_core.schema.authz import (
    CheckAuthorizationRequest
)
from ristops_lib_redis.engine import redis_client

_logger = logging.getLogger(__name__)


async def is_authorized(request: CheckAuthorizationRequest) -> bool:
    _user = await http_service.get(HttpClient.AUTHZ).post(
        url=f"/acl/check",
        json=request.model_dump(mode="json")
    )
    return _user.json().get("is_authorized", False)


async def create_authz_user(user_id: UUID) -> None:
    event = AuthZUserEvent(
        operation=ResourceEventType.CREATED,
        user_id=str(user_id),
    )
    _logger.info("Creating authz user %s", user_id)
    settings = UserProducerSettings.get()
    await redis_client.redis.xadd(
        settings.stream,
        event.model_dump(mode="json"),
        maxlen=10_000,
        approximate=True,
    )


async def delete_authz_user(user_id: UUID) -> None:
    event = AuthZUserEvent(
        operation=ResourceEventType.DELETED,
        user_id=str(user_id),
    )
    _logger.info("Deleting authz user %s", user_id)
    settings = UserProducerSettings.get()
    await redis_client.redis.xadd(
        settings.stream,
        event.model_dump(mode="json"),
        maxlen=10_000,
        approximate=True,
    )

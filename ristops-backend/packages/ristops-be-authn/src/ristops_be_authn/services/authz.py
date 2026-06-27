import logging

from httpx import AsyncClient

from ristops_be_authn.services.http import authz_client
from ristops_be_authn.settings import UserLifecycleProducerSettings
from ristops_lib_be.authz.client import CheckAuthorizationPolicy
from ristops_lib_be.authz.events import UserLifecycleEvent
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_core.schema.user import AppMember
from ristops_lib_redis.engine import redis_client

_logger = logging.getLogger(__name__)


def authz_client_factory() -> AsyncClient:
    return authz_client.client


is_authorized = CheckAuthorizationPolicy(authz_client_factory)


async def publish_user_created_event(info: AppMember) -> None:
    await _publish_user_lifecycle_event(info, LifecycleOperationType.CREATED)


async def publish_user_updated_event(info: AppMember) -> None:
    await _publish_user_lifecycle_event(info, LifecycleOperationType.UPDATED)


async def publish_user_deleted_event(info: AppMember) -> None:
    await _publish_user_lifecycle_event(info, LifecycleOperationType.DELETED)


async def _publish_user_lifecycle_event(info: AppMember, operation: LifecycleOperationType) -> None:
    event = UserLifecycleEvent(
        operation=operation,
        id=info.id,
        username=info.username,
        display_name=info.display_name,
    )
    settings = UserLifecycleProducerSettings.get()
    await redis_client.redis.xadd(
        settings.stream,
        event.model_dump(mode="json"),
        maxlen=10_000,
        approximate=True,
    )
    _logger.info("Published user lifecycle event [%s]: %s", operation, info.id)

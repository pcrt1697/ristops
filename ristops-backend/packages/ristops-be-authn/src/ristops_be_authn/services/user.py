import logging
from uuid import UUID

from ristops_be_authn.settings import UserLifecycleProducerSettings
from ristops_lib_be.authz.events import UserLifecycleEvent
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_redis.engine import redis_client

_logger = logging.getLogger(__name__)


async def publish_user_created_event(user_id: UUID) -> None:
    await _publish_user_lifecycle_event(user_id, LifecycleOperationType.CREATED)


async def publish_user_deleted_event(user_id: UUID) -> None:
    await _publish_user_lifecycle_event(user_id, LifecycleOperationType.DELETED)


async def _publish_user_lifecycle_event(user_id: UUID, operation: LifecycleOperationType) -> None:
    event = UserLifecycleEvent(
        operation=operation,
        user_id=str(user_id),
    )
    settings = UserLifecycleProducerSettings.get()
    await redis_client.redis.xadd(
        settings.stream,
        event.model_dump(mode="json"),
        maxlen=10_000,
        approximate=True,
    )
    _logger.info("Published user lifecycle event %s: %s", operation, user_id)

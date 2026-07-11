import logging

from ristops_be_venue.domain.venue.events import VenueLifecycleEvent
from ristops_be_venue.settings import VenueLifecycleProducerSettings
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_redis.engine import redis_client

_logger = logging.getLogger(__name__)


async def publish_venue_created_event(venue_id: str, timezone: str) -> None:
    await _publish_venue_lifecycle_event(
        venue_id, LifecycleOperationType.CREATED, timezone=timezone, active=True,
    )


async def publish_venue_updated_event(venue_id: str, timezone: str) -> None:
    await _publish_venue_lifecycle_event(
        venue_id, LifecycleOperationType.UPDATED, timezone=timezone, active=True,
    )


async def publish_venue_deleted_event(venue_id: str) -> None:
    await _publish_venue_lifecycle_event(
        venue_id, LifecycleOperationType.DELETED, timezone=None, active=False,
    )


async def _publish_venue_lifecycle_event(
        venue_id: str,
        operation: LifecycleOperationType,
        timezone: str | None,
        active: bool,
) -> None:
    event = VenueLifecycleEvent(
        operation=operation,
        id=venue_id,
        timezone=timezone,
        active=active,
    )
    settings = VenueLifecycleProducerSettings.get()
    await redis_client.redis.xadd(
        settings.stream,
        event.model_dump(mode="json", exclude_none=True),
        maxlen=10_000,
        approximate=True,
    )
    _logger.info("Published venue lifecycle event [%s]: %s", operation, venue_id)

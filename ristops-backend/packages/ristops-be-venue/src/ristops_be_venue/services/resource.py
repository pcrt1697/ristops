import logging

from ristops_be_venue.settings import ResourceLifecycleProducerSettings
from ristops_lib_be.authz.events import (
    ResourceCreatedLifecycleEvent, ResourceDeletedLifecycleEvent,
    ResourceLifecycleEvent
)
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_core.schema.authz import AuthorizationResource, ResourceType
from ristops_lib_redis.engine import redis_client

_logger = logging.getLogger(__name__)


async def publish_resource_created_event(
        resource_id: str,
        resource_type: ResourceType,
        parent_id: str,
        parent_type: ResourceType,
) -> None:
    """Publish a resource-created event to the resource lifecycle stream."""
    event = ResourceCreatedLifecycleEvent(
        operation=LifecycleOperationType.CREATED,
        resources=[AuthorizationResource(
            resource_id=resource_id,
            resource_type=resource_type,
        )],
        parent_id=parent_id,
        parent_type=parent_type,
    )
    await _publish_resource_lifecycle_event(event)
    _logger.info("Published resource creation event for %s: %s", resource_type, resource_id)


async def publish_resource_deleted_event(
        resource_id: str,
        resource_type: ResourceType,
) -> None:
    """Publish a resource-deleted event to the resource lifecycle stream."""
    event = ResourceDeletedLifecycleEvent(
        operation=LifecycleOperationType.DELETED,
        resource_id=resource_id,
        resource_type=resource_type,
    )
    await _publish_resource_lifecycle_event(event)
    _logger.info("Published resource deletion event for %s: %s", resource_type, resource_id)


async def _publish_resource_lifecycle_event(
        event: ResourceLifecycleEvent,
) -> None:
    """Publish a resource lifecycle event to the resource lifecycle stream."""
    settings = ResourceLifecycleProducerSettings.get()
    await redis_client.redis.xadd(
        settings.stream,
        event.model_dump(mode="json", exclude_none=True),
        maxlen=10_000,
        approximate=True,
    )

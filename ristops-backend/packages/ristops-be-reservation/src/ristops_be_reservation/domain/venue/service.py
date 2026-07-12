import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import update, select, ScalarResult
from sqlalchemy.dialects.postgresql import insert

from ristops_be_reservation.domain.venue.entities import VenueEntity
from ristops_be_reservation.domain.venue.events import VenueLifecycleEvent
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_redis.engine import StreamPayload
from ristops_lib_sql.engine import get_sql_session, sql_session_provider

_logger = logging.getLogger(__name__)


async def find_venue_or_throw(venue_id: UUID) -> VenueEntity:
    """Return the local venue read-model for the given ID, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[VenueEntity] = await session.scalars(
        select(VenueEntity).where(VenueEntity.id == venue_id).limit(1)
    )
    venue = result.one_or_none()
    if venue is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Venue not found")
    return venue


async def upsert_venue(venue_id: str, timezone: str, active: bool) -> None:
    """Create or update the local venue read-model. Idempotent: re-running with the same payload is a no-op."""
    session = get_sql_session()
    insert_stmt = insert(VenueEntity).values(
        id=venue_id,
        timezone=timezone,
        active=active,
    )
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=[VenueEntity.id],
        set_={
            "timezone": insert_stmt.excluded.timezone,
            "active": insert_stmt.excluded.active,
        },
    )
    await session.execute(upsert_stmt)
    _logger.info("Upserted venue read-model: %s", venue_id)


async def deactivate_venue(venue_id: str) -> None:
    """Mark the local venue read-model inactive. The row is kept, not removed, since reservation
    config may still reference the venue."""
    session = get_sql_session()
    await session.execute(
        update(VenueEntity).where(VenueEntity.id == venue_id).values(active=False)
    )
    _logger.info("Deactivated venue read-model: %s", venue_id)


async def on_venue_event(_: str, payload: StreamPayload) -> None:
    event = VenueLifecycleEvent.model_validate(payload)
    async with sql_session_provider.context():
        if event.operation in (LifecycleOperationType.CREATED, LifecycleOperationType.UPDATED):
            await upsert_venue(event.id, event.timezone, event.active)
        elif event.operation == LifecycleOperationType.DELETED:
            await deactivate_venue(event.id)

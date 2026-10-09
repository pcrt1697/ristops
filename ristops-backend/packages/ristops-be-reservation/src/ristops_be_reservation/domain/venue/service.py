import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, ScalarResult
from sqlalchemy.dialects.postgresql import insert

from ristops_be_reservation.domain.venue.entities import VenueEntity
from ristops_be_reservation.domain.venue.events import VenueLifecycleEvent
from ristops_be_reservation.domain.venue.models import VenueStatus
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_redis.engine import StreamPayload
from ristops_lib_sql.engine import get_sql_session, sql_session_provider

_logger = logging.getLogger(__name__)


async def find_venue_or_throw(venue_id: UUID, for_update: bool = False) -> VenueEntity:
    """Return the local venue read-model for the given ID, or raise HTTP 404.

    Set ``for_update=True`` from a mutating path that needs to serialize against concurrent
    overlap-checked writes on the same venue: it takes a ``SELECT ... FOR UPDATE`` row lock,
    held until the transaction commits. Leave it false on read paths so plain GETs never block.
    """
    session = get_sql_session()
    stmt = select(VenueEntity).where(VenueEntity.id == venue_id).limit(1)
    if for_update:
        stmt = stmt.with_for_update()
    result: ScalarResult[VenueEntity] = await session.scalars(stmt)
    venue = result.one_or_none()
    if venue is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Venue not found")
    return venue


def check_venue_accepts_config_changes(venue: VenueEntity) -> None:
    """Raise HTTP 409 if the given venue's status doesn't allow config writes (DISABLED or
    CLOSED). PENDING and ACTIVE are allowed — PENDING is exactly the state config is written
    during. Use this directly when the caller already has the venue in hand, to avoid a
    redundant fetch; use `ensure_venue_accepts_config_changes` otherwise."""
    if venue.status in (VenueStatus.DISABLED, VenueStatus.CLOSED):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Venue is {venue.status}; configuration changes are not allowed",
        )


def check_venue_accepts_reservations(venue: VenueEntity) -> None:
    """Raise HTTP 409 unless the venue is ACTIVE. Reservations are only accepted for a live
    venue — deliberately stricter than ``check_venue_accepts_config_changes``, which also allows
    PENDING (a venue still being configured takes no bookings)."""
    if venue.status != VenueStatus.ACTIVE:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Venue is {venue.status}; reservations are not accepted",
        )


async def ensure_venue_accepts_config_changes(venue_id: UUID, for_update: bool = False) -> None:
    """Fetch the venue by ID and raise HTTP 409 if its status doesn't allow config writes.

    Pass ``for_update=True`` from a venue-scoped write to also take the venue row lock in the
    same fetch, serializing concurrent overlap-checked writes across the venue's services.
    """
    venue = await find_venue_or_throw(venue_id, for_update=for_update)
    check_venue_accepts_config_changes(venue)


async def upsert_venue(venue_id: str, timezone: str, status: VenueStatus) -> None:
    """Create or update the local venue read-model. Idempotent: re-running with the same payload is a no-op."""
    session = get_sql_session()
    insert_stmt = insert(VenueEntity).values(
        id=venue_id,
        timezone=timezone,
        status=status,
    )
    upsert_stmt = insert_stmt.on_conflict_do_update(
        index_elements=[VenueEntity.id],
        set_={
            "timezone": insert_stmt.excluded.timezone,
            "status": insert_stmt.excluded.status,
        },
    )
    await session.execute(upsert_stmt)
    _logger.info("Upserted venue read-model: %s", venue_id)


async def on_venue_event(_: str, payload: StreamPayload) -> None:
    event = VenueLifecycleEvent.model_validate(payload)
    async with sql_session_provider.context():
        if event.operation in (LifecycleOperationType.CREATED, LifecycleOperationType.UPDATED):
            await upsert_venue(event.id, event.timezone, event.status)

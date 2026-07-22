import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, ScalarResult, ColumnElement
from sqlalchemy.dialects.postgresql import insert

from ristops_be_reservation.domain.models import normalize_weekdays
from ristops_be_reservation.domain.schedule.schema import DateRangeFilter
from ristops_be_reservation.domain.venue.entities import VenueClosingEntity
from ristops_be_reservation.domain.venue.entities import VenueEntity
from ristops_be_reservation.domain.venue.events import VenueLifecycleEvent
from ristops_be_reservation.domain.venue.models import VenueStatus
from ristops_be_reservation.domain.venue.schema import (
    VenueClosingSearchQuery, VenueClosingResponse,
    VenueClosingUpdateRequest, VenueClosingCreateRequest
)
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_core.schema.pagination import Page
from ristops_lib_redis.engine import StreamPayload
from ristops_lib_sql.engine import get_sql_session, sql_session_provider
from ristops_lib_sql.search import PaginatedSearchQueryExecutor

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


def check_venue_accepts_config_changes(venue: VenueEntity) -> None:
    """Raise HTTP 409 if the given venue's status doesn't allow config writes (DISABLED or
    CLOSED). PENDING and ACTIVE are allowed — PENDING is exactly the state config is written
    during. Use this directly when the caller already has the venue in hand, to avoid a
    redundant fetch; use `ensure_venue_accepts_config_changes` otherwise."""
    if VenueStatus(venue.status) in (VenueStatus.DISABLED, VenueStatus.CLOSED):
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail=f"Venue is {venue.status}; configuration changes are not allowed",
        )


async def ensure_venue_accepts_config_changes(venue_id: UUID) -> None:
    """Fetch the venue by ID and raise HTTP 409 if its status doesn't allow config writes."""
    venue = await find_venue_or_throw(venue_id)
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


# --- Venue-wide closings -----------------------------------------------------

def _venue_date_range_conditions(
        venue_id: UUID,
        date_filter: DateRangeFilter,
) -> list[ColumnElement[bool]]:
    """Scope to the venue and overlap the `[date_from, date_to]` window (either bound optional)."""
    conditions: list[ColumnElement[bool]] = [VenueClosingEntity.venue_id == venue_id]
    if date_filter.date_from is not None:
        conditions.append(VenueClosingEntity.date_end >= date_filter.date_from)
    if date_filter.date_to is not None:
        conditions.append(VenueClosingEntity.date_start <= date_filter.date_to)
    return conditions


_venue_closing_search_executor = PaginatedSearchQueryExecutor[
    VenueClosingSearchQuery, UUID, VenueClosingEntity, VenueClosingResponse
](
    entity_class=VenueClosingEntity,
    response_class=VenueClosingResponse,
    condition_builder=lambda query, venue_id: _venue_date_range_conditions(venue_id, query),
)


async def find_venue_closing_or_throw(venue_id: UUID, closing_id: UUID) -> VenueClosingEntity:
    """Return the venue closing with the given ID under the given venue, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[VenueClosingEntity] = await session.scalars(
        select(VenueClosingEntity).where(
            VenueClosingEntity.id == closing_id,
            VenueClosingEntity.venue_id == venue_id,
        ).limit(1)
    )
    closing = result.one_or_none()
    if closing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Venue closing not found")
    return closing


async def create_venue_closings(
        venue_id: UUID,
        request: VenueClosingCreateRequest,
) -> list[VenueClosingEntity]:
    """Create one or more venue-wide closings in a single transaction — one row per weekday in
    ``request.weekdays`` (normalized: empty/all-seven collapses to a single every-day row).
    Authorized against the venue itself."""
    await ensure_venue_accepts_config_changes(venue_id)
    session = get_sql_session()
    closings = [
        VenueClosingEntity(
            venue_id=venue_id,
            date_start=request.date_start,
            date_end=request.date_end,
            weekday=weekday,
            description=request.description,
        )
        for weekday in normalize_weekdays(request.weekdays)
    ]
    session.add_all(closings)
    await session.flush()
    for closing in closings:
        await session.refresh(closing)
    _logger.info("Created %d venue closing(s) for venue %s", len(closings), venue_id)
    return closings


async def update_venue_closing(
        venue_id: UUID,
        closing_id: UUID,
        request: VenueClosingUpdateRequest,
) -> VenueClosingEntity:
    """Update a venue closing. Only fields present in the request body are modified."""
    closing = await find_venue_closing_or_throw(venue_id, closing_id)
    await ensure_venue_accepts_config_changes(venue_id)
    fields_to_update = request.model_fields_set

    if "date_start" in fields_to_update and request.date_start is not None:
        closing.date_start = request.date_start
    if "date_end" in fields_to_update and request.date_end is not None:
        closing.date_end = request.date_end
    if "weekday" in fields_to_update:
        # Nullable: an explicit null clears the weekday scope (back to every day).
        closing.weekday = request.weekday
    if "description" in fields_to_update:
        closing.description = request.description

    session = get_sql_session()
    await session.flush()
    await session.refresh(closing)
    _logger.info("Updated venue closing %s for venue %s", closing_id, venue_id)
    return closing


async def remove_venue_closing(venue_id: UUID, closing_id: UUID) -> None:
    """Delete a venue closing. Raises HTTP 404 if not found."""
    closing = await find_venue_closing_or_throw(venue_id, closing_id)
    await ensure_venue_accepts_config_changes(venue_id)
    session = get_sql_session()
    await session.delete(closing)
    _logger.info("Deleted venue closing %s for venue %s", closing_id, venue_id)


async def search_venue_closings(
        venue_id: UUID,
        query: VenueClosingSearchQuery,
) -> Page[VenueClosingResponse]:
    """Return a paginated, date-range-filtered page of venue-wide closings for a venue."""
    await find_venue_or_throw(venue_id)
    return await _venue_closing_search_executor.execute(query, venue_id)

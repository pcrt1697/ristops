import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, delete, ScalarResult

from ristops_be_reservation.domain.schedule.entities import (
    OpeningEntity, OpeningOverrideEntity, ClosingEntity,
)
from ristops_be_reservation.domain.schedule.schema import (
    OpeningsUpsertRequest, OpeningOverrideCreateRequest,
    OpeningOverrideUpdateRequest, ClosingCreateRequest, ClosingUpdateRequest,
)
from ristops_be_reservation.domain.service.service import find_service_or_throw
from ristops_be_reservation.domain.venue.service import ensure_venue_accepts_config_changes
from ristops_lib_sql.engine import get_sql_session

_logger = logging.getLogger(__name__)


async def upsert_service_openings(
        service_id: UUID,
        request: OpeningsUpsertRequest,
) -> list[OpeningEntity]:
    """Replace the full set of openings for a service: existing openings are dropped and the
    submitted list is inserted fresh.

    No diff/reconcile-in-place, unlike overrides/closings' per-item CRUD — an opening's `id`
    carries no identity anything else references, so there's nothing to preserve across a
    replace. Duplicate weekdays in the request are rejected at the schema layer
    (`OpeningsUpsertRequest`).
    """
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)

    session = get_sql_session()
    await session.execute(
        delete(OpeningEntity).where(OpeningEntity.service_id == service_id)
    )

    openings = [
        OpeningEntity(
            service_id=service_id,
            weekday=item.weekday,
            capacity=item.capacity,
            start_time=item.start_time,
            end_time=item.end_time,
            description=item.description,
        )
        for item in request.openings
    ]
    session.add_all(openings)

    await session.flush()
    for opening in openings:
        await session.refresh(opening)
    _logger.info("Replaced openings for service %s with %d entries", service_id, len(openings))
    return openings


async def list_service_openings(service_id: UUID, include_deleted: bool = False) -> list[OpeningEntity]:
    """Return all openings for a service."""
    await find_service_or_throw(service_id, include_deleted=include_deleted)
    session = get_sql_session()
    result: ScalarResult[OpeningEntity] = await session.scalars(
        select(OpeningEntity).where(OpeningEntity.service_id == service_id)
    )
    return list(result.all())


async def find_service_opening_override_or_throw(
        service_id: UUID,
        override_id: UUID,
) -> OpeningOverrideEntity:
    """Return the opening override with the given ID under the given service, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[OpeningOverrideEntity] = await session.scalars(
        select(OpeningOverrideEntity).where(
            OpeningOverrideEntity.id == override_id,
            OpeningOverrideEntity.service_id == service_id,
        ).limit(1)
    )
    override = result.one_or_none()
    if override is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Opening override not found")
    return override


async def create_service_opening_override(
        service_id: UUID,
        request: OpeningOverrideCreateRequest,
) -> OpeningOverrideEntity:
    """Create a new opening override for a service. Overrides are one-off special cases, so
    unlike openings this is a plain create, not a bulk reconcile."""
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    override = OpeningOverrideEntity(
        service_id=service_id,
        date_start=request.date_start,
        date_end=request.date_end,
        capacity=request.capacity,
        start_time=request.start_time,
        end_time=request.end_time,
        description=request.description,
    )
    session.add(override)
    await session.flush()
    await session.refresh(override)
    _logger.info("Created opening override %s for service %s", override.id, service_id)
    return override


async def update_service_opening_override(
        service_id: UUID,
        override_id: UUID,
        request: OpeningOverrideUpdateRequest,
) -> OpeningOverrideEntity:
    """Update an opening override. Only fields present in the request body are modified."""
    override = await find_service_opening_override_or_throw(service_id, override_id)
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    fields_to_update = request.model_fields_set

    if "date_start" in fields_to_update and request.date_start is not None:
        override.date_start = request.date_start
    if "date_end" in fields_to_update and request.date_end is not None:
        override.date_end = request.date_end
    if "capacity" in fields_to_update and request.capacity is not None:
        override.capacity = request.capacity
    if "start_time" in fields_to_update and request.start_time is not None:
        override.start_time = request.start_time
    if "end_time" in fields_to_update and request.end_time is not None:
        override.end_time = request.end_time
    if "description" in fields_to_update:
        override.description = request.description

    session = get_sql_session()
    await session.flush()
    await session.refresh(override)
    _logger.info("Updated opening override %s for service %s", override_id, service_id)
    return override


async def remove_service_opening_override(service_id: UUID, override_id: UUID) -> None:
    """Delete an opening override. Raises HTTP 404 if not found."""
    override = await find_service_opening_override_or_throw(service_id, override_id)
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    await session.delete(override)
    _logger.info("Deleted opening override %s for service %s", override_id, service_id)


async def list_service_opening_overrides(
        service_id: UUID,
        include_deleted: bool = False,
) -> list[OpeningOverrideEntity]:
    """Return all opening overrides for a service."""
    await find_service_or_throw(service_id, include_deleted=include_deleted)
    session = get_sql_session()
    result: ScalarResult[OpeningOverrideEntity] = await session.scalars(
        select(OpeningOverrideEntity).where(OpeningOverrideEntity.service_id == service_id)
    )
    return list(result.all())


async def find_service_closing_or_throw(service_id: UUID, closing_id: UUID) -> ClosingEntity:
    """Return the closing with the given ID under the given service, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[ClosingEntity] = await session.scalars(
        select(ClosingEntity).where(
            ClosingEntity.id == closing_id,
            ClosingEntity.service_id == service_id,
        ).limit(1)
    )
    closing = result.one_or_none()
    if closing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Closing not found")
    return closing


async def create_service_closing(
        service_id: UUID,
        request: ClosingCreateRequest,
) -> ClosingEntity:
    """Create a new closing for a service. Closings are one-off special cases, so unlike
    openings this is a plain create, not a bulk reconcile."""
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    closing = ClosingEntity(
        service_id=service_id,
        date_start=request.date_start,
        date_end=request.date_end,
        description=request.description,
    )
    session.add(closing)
    await session.flush()
    await session.refresh(closing)
    _logger.info("Created closing %s for service %s", closing.id, service_id)
    return closing


async def update_service_closing(
        service_id: UUID,
        closing_id: UUID,
        request: ClosingUpdateRequest,
) -> ClosingEntity:
    """Update a closing. Only fields present in the request body are modified."""
    closing = await find_service_closing_or_throw(service_id, closing_id)
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    fields_to_update = request.model_fields_set

    if "date_start" in fields_to_update and request.date_start is not None:
        closing.date_start = request.date_start
    if "date_end" in fields_to_update and request.date_end is not None:
        closing.date_end = request.date_end
    if "description" in fields_to_update:
        closing.description = request.description

    session = get_sql_session()
    await session.flush()
    await session.refresh(closing)
    _logger.info("Updated closing %s for service %s", closing_id, service_id)
    return closing


async def remove_service_closing(service_id: UUID, closing_id: UUID) -> None:
    """Delete a closing. Raises HTTP 404 if not found."""
    closing = await find_service_closing_or_throw(service_id, closing_id)
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    await session.delete(closing)
    _logger.info("Deleted closing %s for service %s", closing_id, service_id)


async def list_service_closings(service_id: UUID, include_deleted: bool = False) -> list[ClosingEntity]:
    """Return all closings for a service."""
    await find_service_or_throw(service_id, include_deleted=include_deleted)
    session = get_sql_session()
    result: ScalarResult[ClosingEntity] = await session.scalars(
        select(ClosingEntity).where(ClosingEntity.service_id == service_id)
    )
    return list(result.all())

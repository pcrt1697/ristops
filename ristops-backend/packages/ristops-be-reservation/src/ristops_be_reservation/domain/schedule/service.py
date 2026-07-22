import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, delete, ScalarResult, ColumnElement

from ristops_be_reservation.domain.models import normalize_weekdays
from ristops_be_reservation.domain.schedule.entities import (
    OpeningEntity, OpeningOverrideEntity, ServiceClosingEntity, CapacityOverrideEntity,
)
from ristops_be_reservation.domain.schedule.schema import (
    OpeningsUpsertRequest, OpeningOverrideCreateRequest,
    OpeningOverrideUpdateRequest, ServiceClosingCreateRequest, ServiceClosingUpdateRequest,
    OpeningOverrideResponse, OpeningOverrideSearchQuery,
    ServiceClosingResponse, ServiceClosingSearchQuery, DateRangeFilter,
    CapacityOverrideCreateRequest, CapacityOverrideUpdateRequest,
    CapacityOverrideResponse, CapacityOverrideSearchQuery,
)
from ristops_be_reservation.domain.service.service import find_service_or_throw
from ristops_be_reservation.domain.venue.service import (
    ensure_venue_accepts_config_changes,
)
from ristops_lib_core.schema.pagination import Page
from ristops_lib_sql.engine import get_sql_session
from ristops_lib_sql.search import PaginatedSearchQueryExecutor

_logger = logging.getLogger(__name__)


def _date_range_conditions(
        entity: type[OpeningOverrideEntity] | type[ServiceClosingEntity] | type[CapacityOverrideEntity],
        service_id: UUID,
        date_filter: DateRangeFilter,
) -> list[ColumnElement[bool]]:
    """Scope to the service and overlap the `[date_from, date_to]` window (either bound
    optional). Overlap = the item's period covers at least one day of the window."""
    conditions: list[ColumnElement[bool]] = [entity.service_id == service_id]
    if date_filter.date_from is not None:
        conditions.append(entity.date_end >= date_filter.date_from)
    if date_filter.date_to is not None:
        conditions.append(entity.date_start <= date_filter.date_to)
    return conditions


_override_search_executor = PaginatedSearchQueryExecutor[
    OpeningOverrideSearchQuery, UUID, OpeningOverrideEntity, OpeningOverrideResponse
](
    entity_class=OpeningOverrideEntity,
    response_class=OpeningOverrideResponse,
    condition_builder=lambda query, service_id: _date_range_conditions(
        OpeningOverrideEntity, service_id, query
    ),
)

_service_closing_search_executor = PaginatedSearchQueryExecutor[
    ServiceClosingSearchQuery, UUID, ServiceClosingEntity, ServiceClosingResponse
](
    entity_class=ServiceClosingEntity,
    response_class=ServiceClosingResponse,
    condition_builder=lambda query, service_id: _date_range_conditions(
        ServiceClosingEntity, service_id, query
    ),
)

_capacity_override_search_executor = PaginatedSearchQueryExecutor[
    CapacityOverrideSearchQuery, UUID, CapacityOverrideEntity, CapacityOverrideResponse
](
    entity_class=CapacityOverrideEntity,
    response_class=CapacityOverrideResponse,
    condition_builder=lambda query, service_id: _date_range_conditions(
        CapacityOverrideEntity, service_id, query
    ),
)


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


async def create_service_opening_overrides(
        service_id: UUID,
        request: OpeningOverrideCreateRequest,
) -> list[OpeningOverrideEntity]:
    """Create one or more opening overrides for a service in a single transaction — one row per
    weekday in ``request.weekdays`` (normalized: empty/all-seven collapses to a single every-day
    row). Overrides are one-off special cases, so unlike openings this is a plain bulk create,
    not a reconcile."""
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    overrides = [
        OpeningOverrideEntity(
            service_id=service_id,
            date_start=request.date_start,
            date_end=request.date_end,
            weekday=weekday,
            capacity=request.capacity,
            start_time=request.start_time,
            end_time=request.end_time,
            description=request.description,
        )
        for weekday in normalize_weekdays(request.weekdays)
    ]
    session.add_all(overrides)
    await session.flush()
    for override in overrides:
        await session.refresh(override)
    _logger.info(
        "Created %d opening override(s) for service %s", len(overrides), service_id
    )
    return overrides


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
    if "weekday" in fields_to_update:
        # Nullable: an explicit null clears the weekday scope (back to every day).
        override.weekday = request.weekday
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


async def search_service_opening_overrides(
        service_id: UUID,
        query: OpeningOverrideSearchQuery,
) -> Page[OpeningOverrideResponse]:
    """Return a paginated, date-range-filtered page of opening overrides for a service."""
    await find_service_or_throw(service_id, include_deleted=query.include_deleted)
    return await _override_search_executor.execute(query, service_id)


async def find_service_closing_or_throw(service_id: UUID, closing_id: UUID) -> ServiceClosingEntity:
    """Return the closing with the given ID under the given service, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[ServiceClosingEntity] = await session.scalars(
        select(ServiceClosingEntity).where(
            ServiceClosingEntity.id == closing_id,
            ServiceClosingEntity.service_id == service_id,
        ).limit(1)
    )
    closing = result.one_or_none()
    if closing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Closing not found")
    return closing


async def create_service_closings(
        service_id: UUID,
        request: ServiceClosingCreateRequest,
) -> list[ServiceClosingEntity]:
    """Create one or more closings for a service in a single transaction — one row per weekday
    in ``request.weekdays`` (normalized: empty/all-seven collapses to a single every-day row).
    Closings are one-off special cases, so unlike openings this is a plain bulk create, not a
    reconcile."""
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    closings = [
        ServiceClosingEntity(
            service_id=service_id,
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
    _logger.info("Created %d closing(s) for service %s", len(closings), service_id)
    return closings


async def update_service_closing(
        service_id: UUID,
        closing_id: UUID,
        request: ServiceClosingUpdateRequest,
) -> ServiceClosingEntity:
    """Update a closing. Only fields present in the request body are modified."""
    closing = await find_service_closing_or_throw(service_id, closing_id)
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
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


async def search_service_closings(
        service_id: UUID,
        query: ServiceClosingSearchQuery,
) -> Page[ServiceClosingResponse]:
    """Return a paginated, date-range-filtered page of closings for a service."""
    await find_service_or_throw(service_id, include_deleted=query.include_deleted)
    return await _service_closing_search_executor.execute(query, service_id)


async def find_service_capacity_override_or_throw(
        service_id: UUID,
        capacity_override_id: UUID,
) -> CapacityOverrideEntity:
    """Return the capacity override with the given ID under the given service, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[CapacityOverrideEntity] = await session.scalars(
        select(CapacityOverrideEntity).where(
            CapacityOverrideEntity.id == capacity_override_id,
            CapacityOverrideEntity.service_id == service_id,
        ).limit(1)
    )
    capacity_override = result.one_or_none()
    if capacity_override is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Capacity override not found")
    return capacity_override


async def create_service_capacity_overrides(
        service_id: UUID,
        request: CapacityOverrideCreateRequest,
) -> list[CapacityOverrideEntity]:
    """Create one or more capacity overrides for a service in a single transaction — one row per
    weekday in ``request.weekdays`` (normalized: empty/all-seven collapses to a single every-day
    row). A one-off seat delta, so a plain bulk create."""
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    capacity_overrides = [
        CapacityOverrideEntity(
            service_id=service_id,
            date_start=request.date_start,
            date_end=request.date_end,
            weekday=weekday,
            capacity_delta=request.capacity_delta,
            description=request.description,
        )
        for weekday in normalize_weekdays(request.weekdays)
    ]
    session.add_all(capacity_overrides)
    await session.flush()
    for capacity_override in capacity_overrides:
        await session.refresh(capacity_override)
    _logger.info(
        "Created %d capacity override(s) for service %s", len(capacity_overrides), service_id
    )
    return capacity_overrides


async def update_service_capacity_override(
        service_id: UUID,
        capacity_override_id: UUID,
        request: CapacityOverrideUpdateRequest,
) -> CapacityOverrideEntity:
    """Update a capacity override. Only fields present in the request body are modified."""
    capacity_override = await find_service_capacity_override_or_throw(service_id, capacity_override_id)
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    fields_to_update = request.model_fields_set

    if "date_start" in fields_to_update and request.date_start is not None:
        capacity_override.date_start = request.date_start
    if "date_end" in fields_to_update and request.date_end is not None:
        capacity_override.date_end = request.date_end
    if "weekday" in fields_to_update:
        # Nullable: an explicit null clears the weekday scope (back to every day).
        capacity_override.weekday = request.weekday
    if "capacity_delta" in fields_to_update and request.capacity_delta is not None:
        capacity_override.capacity_delta = request.capacity_delta
    if "description" in fields_to_update:
        capacity_override.description = request.description

    session = get_sql_session()
    await session.flush()
    await session.refresh(capacity_override)
    _logger.info("Updated capacity override %s for service %s", capacity_override_id, service_id)
    return capacity_override


async def remove_service_capacity_override(service_id: UUID, capacity_override_id: UUID) -> None:
    """Delete a capacity override. Raises HTTP 404 if not found."""
    capacity_override = await find_service_capacity_override_or_throw(service_id, capacity_override_id)
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    await session.delete(capacity_override)
    _logger.info("Deleted capacity override %s for service %s", capacity_override_id, service_id)


async def search_service_capacity_overrides(
        service_id: UUID,
        query: CapacityOverrideSearchQuery,
) -> Page[CapacityOverrideResponse]:
    """Return a paginated, date-range-filtered page of capacity overrides for a service."""
    await find_service_or_throw(service_id, include_deleted=query.include_deleted)
    return await _capacity_override_search_executor.execute(query, service_id)

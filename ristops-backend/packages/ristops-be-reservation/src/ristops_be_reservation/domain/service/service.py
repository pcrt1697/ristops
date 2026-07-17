import logging
from datetime import datetime, UTC
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, delete, ScalarResult, ColumnElement

from ristops_be_reservation.domain.service.entities import (
    ServiceEntity, ServiceOpeningEntity, ServiceOpeningOverrideEntity, ServiceClosingEntity,
)
from ristops_be_reservation.domain.service.schema import (
    ServiceCreationRequest, ServiceResponse, ServiceListQuery, ServiceOpeningsUpsertRequest,
    ServiceOpeningOverrideCreateRequest, ServiceOpeningOverrideUpdateRequest,
    ServiceClosingCreateRequest, ServiceClosingUpdateRequest,
)
from ristops_be_reservation.domain.venue.service import (
    find_venue_or_throw, check_venue_accepts_config_changes, ensure_venue_accepts_config_changes,
)
from ristops_be_reservation.services.resource import publish_resource_created_event, publish_resource_deleted_event
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_sql.engine import get_sql_session
from ristops_lib_sql.search import SearchQueryExecutor

_logger = logging.getLogger(__name__)


async def create_service(request: ServiceCreationRequest) -> ServiceEntity:
    """Create a new service under a venue."""
    venue = await find_venue_or_throw(request.venue_id)
    check_venue_accepts_config_changes(venue)
    session = get_sql_session()
    service = ServiceEntity(
        venue_id=request.venue_id,
        name=request.name,
        description=request.description,
        turn_time_m=request.turn_time_m,
        advance_notice_m=request.advance_notice_m,
        slot_interval_m=request.slot_interval_m,
        grace_period_m=request.grace_period_m,
    )
    session.add(service)
    await session.flush()
    await session.refresh(service)
    await publish_resource_created_event(
        str(service.id),
        ResourceType.SERVICE,
        str(request.venue_id),
        ResourceType.VENUE,
    )
    _logger.info("Created service: %s", service.id)
    return service


async def find_service_or_throw(service_id: UUID, include_deleted: bool = False) -> ServiceEntity:
    """Return the service with the given ID, or raise HTTP 404.

    Deleted services are excluded by default; set ``include_deleted=True`` to fetch them anyway
    (e.g. to resolve a service still referenced by an existing reservation).
    """
    session = get_sql_session()
    conditions = [ServiceEntity.id == service_id]
    if not include_deleted:
        conditions.append(ServiceEntity.deleted_at.is_(None))
    result: ScalarResult[ServiceEntity] = await session.scalars(
        select(ServiceEntity).where(*conditions).limit(1)
    )
    service = result.one_or_none()
    if service is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Service not found")
    return service


def _build_service_conditions(query: ServiceListQuery, scope: None) -> list[ColumnElement[bool]]:
    """Build the WHERE conditions from the user filter."""
    conditions = [ServiceEntity.venue_id == query.venue_id]
    if query.name is not None:
        conditions.append(ServiceEntity.name.ilike(f"%{query.name}%"))
    if not query.include_deleted:
        conditions.append(ServiceEntity.deleted_at.is_(None))
    return conditions


_service_list_executor: SearchQueryExecutor[ServiceListQuery, None, ServiceEntity, ServiceResponse] = (
    SearchQueryExecutor(
        entity_class=ServiceEntity,
        response_class=ServiceResponse,
        condition_builder=_build_service_conditions,
    )
)


async def list_services(query: ServiceListQuery) -> list[ServiceResponse]:
    """Return services matching the given filters, sorted per the query. Not paginated."""
    return await _service_list_executor.execute(query, None)


async def upsert_service_openings(
        service_id: UUID,
        request: ServiceOpeningsUpsertRequest,
) -> list[ServiceOpeningEntity]:
    """Replace the full set of openings for a service: existing openings are dropped and the
    submitted list is inserted fresh.

    No diff/reconcile-in-place, unlike overrides/closings' per-item CRUD — an opening's `id`
    carries no identity anything else references, so there's nothing to preserve across a
    replace. Duplicate weekdays in the request are rejected at the schema layer
    (`ServiceOpeningsUpsertRequest`).
    """
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)

    session = get_sql_session()
    await session.execute(
        delete(ServiceOpeningEntity).where(ServiceOpeningEntity.service_id == service_id)
    )

    openings = [
        ServiceOpeningEntity(
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


async def list_service_openings(service_id: UUID, include_deleted: bool = False) -> list[ServiceOpeningEntity]:
    """Return all openings for a service."""
    await find_service_or_throw(service_id, include_deleted=include_deleted)
    session = get_sql_session()
    result: ScalarResult[ServiceOpeningEntity] = await session.scalars(
        select(ServiceOpeningEntity).where(ServiceOpeningEntity.service_id == service_id)
    )
    return list(result.all())


async def find_service_opening_override_or_throw(
        service_id: UUID,
        override_id: UUID,
) -> ServiceOpeningOverrideEntity:
    """Return the opening override with the given ID under the given service, or raise HTTP 404."""
    session = get_sql_session()
    result: ScalarResult[ServiceOpeningOverrideEntity] = await session.scalars(
        select(ServiceOpeningOverrideEntity).where(
            ServiceOpeningOverrideEntity.id == override_id,
            ServiceOpeningOverrideEntity.service_id == service_id,
        ).limit(1)
    )
    override = result.one_or_none()
    if override is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Opening override not found")
    return override


async def create_service_opening_override(
        service_id: UUID,
        request: ServiceOpeningOverrideCreateRequest,
) -> ServiceOpeningOverrideEntity:
    """Create a new opening override for a service. Overrides are one-off special cases, so
    unlike openings this is a plain create, not a bulk reconcile."""
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    override = ServiceOpeningOverrideEntity(
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
        request: ServiceOpeningOverrideUpdateRequest,
) -> ServiceOpeningOverrideEntity:
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
) -> list[ServiceOpeningOverrideEntity]:
    """Return all opening overrides for a service."""
    await find_service_or_throw(service_id, include_deleted=include_deleted)
    session = get_sql_session()
    result: ScalarResult[ServiceOpeningOverrideEntity] = await session.scalars(
        select(ServiceOpeningOverrideEntity).where(ServiceOpeningOverrideEntity.service_id == service_id)
    )
    return list(result.all())


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


async def create_service_closing(
        service_id: UUID,
        request: ServiceClosingCreateRequest,
) -> ServiceClosingEntity:
    """Create a new closing for a service. Closings are one-off special cases, so unlike
    openings this is a plain create, not a bulk reconcile."""
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    session = get_sql_session()
    closing = ServiceClosingEntity(
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


async def list_service_closings(service_id: UUID, include_deleted: bool = False) -> list[ServiceClosingEntity]:
    """Return all closings for a service."""
    await find_service_or_throw(service_id, include_deleted=include_deleted)
    session = get_sql_session()
    result: ScalarResult[ServiceClosingEntity] = await session.scalars(
        select(ServiceClosingEntity).where(ServiceClosingEntity.service_id == service_id)
    )
    return list(result.all())


async def remove_service(service_id: UUID) -> None:
    """Soft-delete the service with the given ID. Raises HTTP 404 if not found."""
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    service.deleted_at = datetime.now(UTC)
    session = get_sql_session()
    await session.flush()
    await publish_resource_deleted_event(str(service_id), ResourceType.SERVICE)
    _logger.info("Deleted service: %s", service_id)

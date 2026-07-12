import logging
from datetime import datetime, UTC
from http import HTTPStatus
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import select, ScalarResult, ColumnElement

from ristops_be_reservation.domain.service.entities import (
    ServiceEntity, ServiceOpeningEntity, ServiceOpeningOverrideEntity, ServiceClosingEntity,
)
from ristops_be_reservation.domain.service.schema import (
    ServiceCreationRequest, ServiceResponse, ServiceSearchQuery, ServiceOpeningUpsertRequest,
    ServiceOpeningOverrideUpsertRequest, ServiceClosingUpsertRequest,
)
from ristops_be_reservation.domain.venue.service import find_venue_or_throw
from ristops_be_reservation.services.resource import publish_resource_created_event, publish_resource_deleted_event
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_sql.engine import get_sql_session
from ristops_lib_sql.search import SearchQueryExecutor

_logger = logging.getLogger(__name__)


async def create_service(request: ServiceCreationRequest) -> ServiceEntity:
    """Create a new service under a venue."""
    await find_venue_or_throw(request.venue_id)
    session = get_sql_session()
    service = ServiceEntity(
        id=uuid4(),
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


def _build_service_conditions(query: ServiceSearchQuery, scope: None) -> list[ColumnElement[bool]]:
    """Build the WHERE conditions from the user filter."""
    conditions = [ServiceEntity.venue_id == query.venue_id]
    if query.name is not None:
        conditions.append(ServiceEntity.name.ilike(f"%{query.name}%"))
    if not query.include_deleted:
        conditions.append(ServiceEntity.deleted_at.is_(None))
    return conditions


_service_search_executor: SearchQueryExecutor[ServiceSearchQuery, None, ServiceEntity, ServiceResponse] = (
    SearchQueryExecutor(
        entity_class=ServiceEntity,
        response_class=ServiceResponse,
        condition_builder=_build_service_conditions,
    )
)


async def search_services(query: ServiceSearchQuery) -> list[ServiceResponse]:
    """Return services matching the given filters, sorted per the query. Not paginated."""
    return await _service_search_executor.execute(query, None)


async def upsert_service_openings(
        service_id: UUID,
        requests: list[ServiceOpeningUpsertRequest],
) -> list[ServiceOpeningEntity]:
    """Replace the full set of openings for a service with the given list.

    Reconciled by weekday, the natural key now that openings are periodless (unique per
    (service_id, weekday)): submitted weekdays are created or updated in place, and any
    existing opening whose weekday is absent from the list is deleted.
    """
    await find_service_or_throw(service_id)

    weekdays = [request.weekday for request in requests]
    if len(weekdays) != len(set(weekdays)):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Duplicate weekday in openings list",
        )

    session = get_sql_session()
    existing_result: ScalarResult[ServiceOpeningEntity] = await session.scalars(
        select(ServiceOpeningEntity).where(ServiceOpeningEntity.service_id == service_id)
    )
    existing_by_weekday = {opening.weekday: opening for opening in existing_result.all()}

    submitted_weekdays = set(weekdays)
    for weekday, opening in existing_by_weekday.items():
        if weekday not in submitted_weekdays:
            await session.delete(opening)

    openings = []
    for request in requests:
        opening = existing_by_weekday.get(request.weekday)
        if opening is None:
            opening = ServiceOpeningEntity(
                id=uuid4(),
                service_id=service_id,
                weekday=request.weekday,
            )
            session.add(opening)
        opening.capacity = request.capacity
        opening.start_time = request.start_time
        opening.end_time = request.end_time
        opening.description = request.description
        openings.append(opening)

    await session.flush()
    for opening in openings:
        await session.refresh(opening)
    _logger.info("Upserted %d openings for service %s", len(openings), service_id)
    return openings


async def list_service_openings(service_id: UUID, include_deleted: bool = False) -> list[ServiceOpeningEntity]:
    """Return all openings for a service."""
    await find_service_or_throw(service_id, include_deleted=include_deleted)
    session = get_sql_session()
    result: ScalarResult[ServiceOpeningEntity] = await session.scalars(
        select(ServiceOpeningEntity).where(ServiceOpeningEntity.service_id == service_id)
    )
    return list(result.all())


async def upsert_service_opening_overrides(
        service_id: UUID,
        requests: list[ServiceOpeningOverrideUpsertRequest],
) -> list[ServiceOpeningOverrideEntity]:
    """Replace the full set of opening overrides for a service with the given list.

    Reconciled by id, since overrides have no natural business key (a service may have many,
    non-overlapping date ranges): items with an id update the matching existing row, items
    without an id are created, and existing rows whose id is absent from the list are deleted.
    """
    await find_service_or_throw(service_id)

    ids = [request.id for request in requests if request.id is not None]
    if len(ids) != len(set(ids)):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Duplicate id in opening overrides list",
        )

    session = get_sql_session()
    existing_result: ScalarResult[ServiceOpeningOverrideEntity] = await session.scalars(
        select(ServiceOpeningOverrideEntity).where(ServiceOpeningOverrideEntity.service_id == service_id)
    )
    existing_by_id = {override.id: override for override in existing_result.all()}

    submitted_ids = set(ids)
    for existing_id, override in existing_by_id.items():
        if existing_id not in submitted_ids:
            await session.delete(override)

    overrides = []
    for request in requests:
        if request.id is not None:
            override = existing_by_id.get(request.id)
            if override is None:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Opening override {request.id} not found for this service",
                )
        else:
            override = ServiceOpeningOverrideEntity(id=uuid4(), service_id=service_id)
            session.add(override)
        override.date_start = request.date_start
        override.date_end = request.date_end
        override.capacity = request.capacity
        override.start_time = request.start_time
        override.end_time = request.end_time
        override.description = request.description
        overrides.append(override)

    await session.flush()
    for override in overrides:
        await session.refresh(override)
    _logger.info("Upserted %d opening overrides for service %s", len(overrides), service_id)
    return overrides


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


async def upsert_service_closings(
        service_id: UUID,
        requests: list[ServiceClosingUpsertRequest],
) -> list[ServiceClosingEntity]:
    """Replace the full set of closings for a service with the given list.

    Reconciled by id, since closings have no natural business key: items with an id update the
    matching existing row, items without an id are created, and existing rows whose id is
    absent from the list are deleted.
    """
    await find_service_or_throw(service_id)

    ids = [request.id for request in requests if request.id is not None]
    if len(ids) != len(set(ids)):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail="Duplicate id in closings list",
        )

    session = get_sql_session()
    existing_result: ScalarResult[ServiceClosingEntity] = await session.scalars(
        select(ServiceClosingEntity).where(ServiceClosingEntity.service_id == service_id)
    )
    existing_by_id = {closing.id: closing for closing in existing_result.all()}

    submitted_ids = set(ids)
    for existing_id, closing in existing_by_id.items():
        if existing_id not in submitted_ids:
            await session.delete(closing)

    closings = []
    for request in requests:
        if request.id is not None:
            closing = existing_by_id.get(request.id)
            if closing is None:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST,
                    detail=f"Closing {request.id} not found for this service",
                )
        else:
            closing = ServiceClosingEntity(id=uuid4(), service_id=service_id)
            session.add(closing)
        closing.date_start = request.date_start
        closing.date_end = request.date_end
        closing.description = request.description
        closings.append(closing)

    await session.flush()
    for closing in closings:
        await session.refresh(closing)
    _logger.info("Upserted %d closings for service %s", len(closings), service_id)
    return closings


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
    service.deleted_at = datetime.now(UTC)
    session = get_sql_session()
    await session.flush()
    await publish_resource_deleted_event(str(service_id), ResourceType.SERVICE)
    _logger.info("Deleted service: %s", service_id)

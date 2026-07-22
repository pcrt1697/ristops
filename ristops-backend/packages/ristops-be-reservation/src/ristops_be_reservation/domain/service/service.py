import logging
from datetime import datetime, UTC
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, ScalarResult, ColumnElement

from ristops_be_reservation.domain.service.entities import ServiceEntity
from ristops_be_reservation.domain.service.schema import (
    ServiceCreationRequest, ServiceUpdateRequest, ServiceResponse, ServiceListQuery,
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


async def update_service(service_id: UUID, request: ServiceUpdateRequest) -> ServiceEntity:
    """Update a service. Only fields present in the request body are modified. Raises HTTP 404
    if the service is not found, or HTTP 409 if its venue is not accepting config changes."""
    service = await find_service_or_throw(service_id)
    check_venue_accepts_config_changes(await find_venue_or_throw(service.venue_id))
    fields_to_update = request.model_fields_set

    if "name" in fields_to_update and request.name is not None:
        service.name = request.name
    if "description" in fields_to_update:
        service.description = request.description
    if "turn_time_m" in fields_to_update and request.turn_time_m is not None:
        service.turn_time_m = request.turn_time_m
    if "advance_notice_m" in fields_to_update and request.advance_notice_m is not None:
        service.advance_notice_m = request.advance_notice_m
    if "slot_interval_m" in fields_to_update and request.slot_interval_m is not None:
        service.slot_interval_m = request.slot_interval_m
    if "grace_period_m" in fields_to_update and request.grace_period_m is not None:
        service.grace_period_m = request.grace_period_m

    session = get_sql_session()
    await session.flush()
    await session.refresh(service)
    _logger.info("Updated service: %s", service_id)
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


async def remove_service(service_id: UUID) -> None:
    """Soft-delete the service with the given ID. Raises HTTP 404 if not found."""
    service = await find_service_or_throw(service_id)
    await ensure_venue_accepts_config_changes(service.venue_id)
    service.deleted_at = datetime.now(UTC)
    session = get_sql_session()
    await session.flush()
    await publish_resource_deleted_event(str(service_id), ResourceType.SERVICE)
    _logger.info("Deleted service: %s", service_id)

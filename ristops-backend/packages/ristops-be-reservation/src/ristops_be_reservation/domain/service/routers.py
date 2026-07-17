from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.params import Path

from ristops_be_reservation.domain.service.schema import (
    ServiceCreationRequest, ServiceResponse, ServicesResponse, ServiceListQuery,
    ServiceOpeningsUpsertRequest, ServiceOpeningsResponse, ServiceOpeningResponse,
    ServiceOpeningOverrideCreateRequest, ServiceOpeningOverrideUpdateRequest,
    ServiceOpeningOverrideResponse, ServiceOpeningOverridesResponse,
    ServiceClosingCreateRequest, ServiceClosingUpdateRequest, ServiceClosingResponse,
    ServiceClosingsResponse,
)
from ristops_be_reservation.domain.service.service import (
    create_service, find_service_or_throw, remove_service, list_services,
    upsert_service_openings, list_service_openings,
    create_service_opening_override, update_service_opening_override,
    remove_service_opening_override, list_service_opening_overrides,
    create_service_closing, update_service_closing,
    remove_service_closing, list_service_closings,
)
from ristops_lib_be.authz.policy import (
    policy, BaseResourceResolver, Policy, resolve_body_attribute, resolve_query_attribute,
)
from ristops_lib_core.exception import ErrorResponse
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_sql.engine import sql_transactional

_venue_body_resolver = BaseResourceResolver(ResourceType.VENUE, resolver=resolve_body_attribute)
_venue_query_resolver = BaseResourceResolver(
    ResourceType.VENUE, field="filter.venue_id", resolver=resolve_query_attribute,
)
_service_path_resolver = BaseResourceResolver(ResourceType.SERVICE)
service_router = APIRouter(
    prefix="/services",
    tags=["services"],
)


@service_router.get(
    "",
    response_model=ServicesResponse,
)
@policy(Policy(_venue_query_resolver, "service:list"))
@sql_transactional
async def get_services(
        query: Annotated[ServiceListQuery, Query()],
) -> ServicesResponse:
    """Return services for a venue matching the given filters, sorted per the query.
    Not paginated. Authorized against the venue."""
    services = await list_services(query)
    return ServicesResponse(services=services)


@service_router.post(
    "",
    response_model=ServiceResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_venue_body_resolver, "service:add"))
@sql_transactional
async def create(
        request: ServiceCreationRequest,
) -> ServiceResponse:
    """Create a new service under a venue. Authorized against the venue, since the service
    does not exist yet."""
    service = await create_service(request)
    return ServiceResponse.model_validate(service, from_attributes=True)


@service_router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:get"))
@sql_transactional
async def get(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return the service even if it has been deleted")
        ] = False,
) -> ServiceResponse:
    """Return a service by ID. Authorized against the service itself, inheriting grants from
    its venue via the ReBAC hierarchy."""
    service = await find_service_or_throw(service_id, include_deleted=include_deleted)
    return ServiceResponse.model_validate(service, from_attributes=True)


@service_router.delete(
    "/{service_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:remove"))
@sql_transactional
async def delete(
        service_id: Annotated[UUID, Path(description="Service ID")],
) -> None:
    """Delete a service by ID. Authorized against the service itself."""
    await remove_service(service_id)


@service_router.put(
    "/{service_id}/openings",
    response_model=ServiceOpeningsResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
        HTTPStatus.UNPROCESSABLE_ENTITY: {
            "model": ErrorResponse, "description": "Duplicate weekday in openings list",
        },
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def upsert_openings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: ServiceOpeningsUpsertRequest,
) -> ServiceOpeningsResponse:
    """Replace the full set of openings for a service with the given list: openings for
    weekdays present in the list are created or updated, openings for weekdays absent from
    the list are deleted. Authorized against the service itself."""
    openings = await upsert_service_openings(service_id, request)
    return ServiceOpeningsResponse(
        openings=[ServiceOpeningResponse.model_validate(opening, from_attributes=True) for opening in openings]
    )


@service_router.get(
    "/{service_id}/openings",
    response_model=ServiceOpeningsResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:get"))
@sql_transactional
async def get_service_openings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return openings even if the service has been deleted")
        ] = False,
) -> ServiceOpeningsResponse:
    """Return all openings for a service. Authorized against the service itself."""
    openings = await list_service_openings(service_id, include_deleted=include_deleted)
    return ServiceOpeningsResponse(
        openings=[ServiceOpeningResponse.model_validate(opening, from_attributes=True) for opening in openings]
    )


@service_router.post(
    "/{service_id}/opening-overrides",
    response_model=ServiceOpeningOverrideResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def create_opening_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: ServiceOpeningOverrideCreateRequest,
) -> ServiceOpeningOverrideResponse:
    """Create a new opening override for a service. Authorized against the service itself."""
    override = await create_service_opening_override(service_id, request)
    return ServiceOpeningOverrideResponse.model_validate(override, from_attributes=True)


@service_router.patch(
    "/{service_id}/opening-overrides/{override_id}",
    response_model=ServiceOpeningOverrideResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Opening override not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def update_opening_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        override_id: Annotated[UUID, Path(description="Opening override ID")],
        request: ServiceOpeningOverrideUpdateRequest,
) -> ServiceOpeningOverrideResponse:
    """Update an opening override. Only fields present in the request body are modified.
    Authorized against the service itself."""
    override = await update_service_opening_override(service_id, override_id, request)
    return ServiceOpeningOverrideResponse.model_validate(override, from_attributes=True)


@service_router.delete(
    "/{service_id}/opening-overrides/{override_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Opening override not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def delete_opening_override(
        service_id: Annotated[UUID, Path(description="Service ID")],
        override_id: Annotated[UUID, Path(description="Opening override ID")],
) -> None:
    """Delete an opening override. Authorized against the service itself."""
    await remove_service_opening_override(service_id, override_id)


@service_router.get(
    "/{service_id}/opening-overrides",
    response_model=ServiceOpeningOverridesResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:get"))
@sql_transactional
async def get_service_opening_overrides(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return opening overrides even if the service has been deleted")
        ] = False,
) -> ServiceOpeningOverridesResponse:
    """Return all opening overrides for a service. Authorized against the service itself."""
    overrides = await list_service_opening_overrides(service_id, include_deleted=include_deleted)
    return ServiceOpeningOverridesResponse(
        opening_overrides=[
            ServiceOpeningOverrideResponse.model_validate(override, from_attributes=True) for override in overrides
        ]
    )


@service_router.post(
    "/{service_id}/closings",
    response_model=ServiceClosingResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def create_closing(
        service_id: Annotated[UUID, Path(description="Service ID")],
        request: ServiceClosingCreateRequest,
) -> ServiceClosingResponse:
    """Create a new closing for a service. Authorized against the service itself."""
    closing = await create_service_closing(service_id, request)
    return ServiceClosingResponse.model_validate(closing, from_attributes=True)


@service_router.patch(
    "/{service_id}/closings/{closing_id}",
    response_model=ServiceClosingResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Closing not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def update_closing(
        service_id: Annotated[UUID, Path(description="Service ID")],
        closing_id: Annotated[UUID, Path(description="Closing ID")],
        request: ServiceClosingUpdateRequest,
) -> ServiceClosingResponse:
    """Update a closing. Only fields present in the request body are modified. Authorized
    against the service itself."""
    closing = await update_service_closing(service_id, closing_id, request)
    return ServiceClosingResponse.model_validate(closing, from_attributes=True)


@service_router.delete(
    "/{service_id}/closings/{closing_id}",
    status_code=HTTPStatus.NO_CONTENT,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Closing not found"},
        HTTPStatus.CONFLICT: {"model": ErrorResponse, "description": "Venue is not accepting config changes"},
    },
)
@policy(Policy(_service_path_resolver, "service:edit"))
@sql_transactional
async def delete_closing(
        service_id: Annotated[UUID, Path(description="Service ID")],
        closing_id: Annotated[UUID, Path(description="Closing ID")],
) -> None:
    """Delete a closing. Authorized against the service itself."""
    await remove_service_closing(service_id, closing_id)


@service_router.get(
    "/{service_id}/closings",
    response_model=ServiceClosingsResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Service not found"},
    },
)
@policy(Policy(_service_path_resolver, "service:get"))
@sql_transactional
async def get_service_closings(
        service_id: Annotated[UUID, Path(description="Service ID")],
        include_deleted: Annotated[
            bool, Query(description="Return closings even if the service has been deleted")
        ] = False,
) -> ServiceClosingsResponse:
    """Return all closings for a service. Authorized against the service itself."""
    closings = await list_service_closings(service_id, include_deleted=include_deleted)
    return ServiceClosingsResponse(
        closings=[ServiceClosingResponse.model_validate(closing, from_attributes=True) for closing in closings]
    )

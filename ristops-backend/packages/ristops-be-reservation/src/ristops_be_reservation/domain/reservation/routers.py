from http import HTTPStatus
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query
from fastapi.params import Path

from ristops_be_reservation.domain.reservation.schema import (
    ReservationCreationRequest, ReservationUpdateRequest, ReservationResponse, ReservationSearchQuery,
    ReservationActionRequest, ReservationActionType, CalendarQuery, CalendarResponse,
)
from ristops_be_reservation.domain.reservation.service import (
    create_reservation, get_reservation, update_reservation, list_reservations,
    update_reservation_status, list_calendar_days,
)
from ristops_lib_be.authz.policy import (
    policy, BaseResourceResolver, Policy, resolve_body_attribute, resolve_query_attribute,
    resolve_permission_from_body_field,
)
from ristops_lib_core.exception import ErrorResponse
from ristops_lib_core.schema.authz import ResourceType
from ristops_lib_core.schema.pagination import Page
from ristops_lib_sql.engine import sql_transactional

_venue_body_resolver = BaseResourceResolver(ResourceType.VENUE, resolver=resolve_body_attribute)
_venue_query_resolver = BaseResourceResolver(
    ResourceType.VENUE, field="filter.venue_id", resolver=resolve_query_attribute,
)
_venue_plain_query_resolver = BaseResourceResolver(
    ResourceType.VENUE, field="venue_id", resolver=resolve_query_attribute,
)
_reservation_path_resolver = BaseResourceResolver(ResourceType.RESERVATION)

# The `/actions` endpoint requires a different permission per action, resolved from the request
# body's `action` discriminator (mirrors be-venue's perform_action). An unmapped action is
# rejected with 400.
_reservation_action_permission_resolver = resolve_permission_from_body_field(
    "action",
    {
        ReservationActionType.CONFIRM: "reservation:confirm",
        ReservationActionType.REJECT: "reservation:reject",
        ReservationActionType.CANCEL: "reservation:cancel",
        ReservationActionType.CHECK_IN: "reservation:check-in",
        ReservationActionType.NO_SHOW: "reservation:no-show",
        ReservationActionType.WITHDRAW: "reservation:withdraw",
    },
)
reservation_router = APIRouter(
    prefix="/reservations",
    tags=["reservations"],
)


@reservation_router.get(
    "/calendar",
    response_model=CalendarResponse,
)
@policy(Policy(_venue_plain_query_resolver, "reservation:list"))
@sql_transactional
async def calendar(
        query: Annotated[CalendarQuery, Query()],
) -> CalendarResponse:
    """Per-day, per-service occupancy of a venue over a date window: which services run each day,
    their hours, and how many seats are taken. Also the source of what is still bookable on a
    day. Authorized against the venue."""
    return await list_calendar_days(query)


@reservation_router.get(
    "/{reservation_id}",
    response_model=ReservationResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Reservation not found"},
    },
)
@policy(Policy(_reservation_path_resolver, "reservation:get"))
@sql_transactional
async def get(
        reservation_id: Annotated[UUID, Path(description="Reservation ID")],
) -> ReservationResponse:
    """Return a reservation by ID. Authorized against the reservation itself, inheriting grants
    from its venue via the ReBAC hierarchy."""
    return await get_reservation(reservation_id)


@reservation_router.get(
    "",
    response_model=Page[ReservationResponse],
)
@policy(Policy(_venue_query_resolver, "reservation:list"))
@sql_transactional
async def get_reservations(
        query: Annotated[ReservationSearchQuery, Query()],
) -> Page[ReservationResponse]:
    """Return reservations for a venue matching the given filters, sorted and paginated per the
    query. Authorized against the venue."""
    return await list_reservations(query)


@reservation_router.post(
    "",
    response_model=ReservationResponse,
    status_code=HTTPStatus.CREATED,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Venue or service not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting reservations, the service is not open at the "
                           "requested time, or not enough seats remain",
        },
    },
)
@policy(Policy(_venue_body_resolver, "reservation:add"))
@sql_transactional
async def create(
        request: ReservationCreationRequest,
) -> ReservationResponse:
    """Book a reservation into one of a venue's services. Authorized against the venue, since the
    reservation does not exist yet."""
    return await create_reservation(request)


@reservation_router.patch(
    "/{reservation_id}",
    response_model=ReservationResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Reservation not found"},
        HTTPStatus.CONFLICT: {
            "model": ErrorResponse,
            "description": "Venue is not accepting reservations, the service is not open at the "
                           "new time, or not enough seats remain",
        },
    },
)
@policy(Policy(_reservation_path_resolver, "reservation:edit"))
@sql_transactional
async def update(
        reservation_id: Annotated[UUID, Path(description="Reservation ID")],
        request: ReservationUpdateRequest,
) -> ReservationResponse:
    """Update a reservation. Only fields present in the request body are modified; changing the
    time or party size re-validates the booking against its service. Authorized against the
    reservation itself."""
    return await update_reservation(reservation_id, request)


@reservation_router.post(
    "/{reservation_id}/actions",
    response_model=ReservationResponse,
    responses={
        HTTPStatus.NOT_FOUND: {"model": ErrorResponse, "description": "Reservation not found"},
        HTTPStatus.BAD_REQUEST: {
            "model": ErrorResponse, "description": "Unknown action",
        },
    },
)
@policy(Policy(
    _reservation_path_resolver,
    permissions_resolver=_reservation_action_permission_resolver,
))
@sql_transactional
async def actions(
        reservation_id: Annotated[UUID, Path(description="Reservation ID")],
        request: ReservationActionRequest,
) -> ReservationResponse:
    """Apply a status-change action to a reservation (confirm/reject/cancel/check-in/no-show/
    withdraw). The request body is discriminated on ``action`` (the verb); the required permission
    is resolved per action (e.g. ``reservation:confirm``), authorized against the reservation
    itself. A check-in also records the arrival time; any action may attach ``notes``."""
    return await update_reservation_status(reservation_id, request)

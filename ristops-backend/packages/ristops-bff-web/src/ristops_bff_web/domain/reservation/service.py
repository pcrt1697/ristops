from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from ristops_bff_web.http import reservation_client
from ristops_lib_core.http import ResponseTransformer

reservation_transformer = ResponseTransformer(
    reservation_date=datetime.fromisoformat,
    arrival_time=time.fromisoformat,
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
)

over_capacity_transformer = ResponseTransformer(
    business_date=date.fromisoformat,
)


async def find_reservation(reservation_id: str | UUID) -> dict[str, Any]:
    """Fetch a single reservation (with its computed violation, if any)."""
    response = await reservation_client.client.get(url=f"reservations/{reservation_id}")
    return reservation_transformer.get_json(response)


async def search_reservations(params: dict[str, Any]) -> dict[str, Any]:
    """Search a venue's reservations; each item carries a computed `violation`."""
    response = await reservation_client.client.get(url="reservations", params=params)
    page = response.json()
    page["items"] = [reservation_transformer.transform(item) for item in page["items"]]
    return page


async def create_reservation(payload: dict[str, Any]) -> dict[str, Any]:
    """Create a reservation; the backend infers the service from venue + datetime."""
    response = await reservation_client.client.post(url="reservations", json=payload)
    return reservation_transformer.get_json(response)


async def update_reservation(reservation_id: str | UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Update a reservation's editable fields."""
    response = await reservation_client.client.patch(
        url=f"reservations/{reservation_id}", json=payload,
    )
    return reservation_transformer.get_json(response)


async def perform_reservation_action(reservation_id: str | UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Apply a status-change action (confirm/reject/cancel/check-in/no-show/withdraw). The body's
    `status` selects the action; the backend resolves the required permission from it."""
    response = await reservation_client.client.post(
        url=f"reservations/{reservation_id}/actions", json=payload,
    )
    return reservation_transformer.get_json(response)


async def reservation_over_capacity(venue_id: str | UUID) -> list[dict[str, Any]]:
    """Slots of the venue whose live bookings now exceed the effective capacity."""
    response = await reservation_client.client.get(
        url="reservations/over-capacity", params={"venue_id": str(venue_id)},
    )
    slots = response.json()["slots"]
    return [over_capacity_transformer.transform(slot) for slot in slots]


calendar_day_transformer = ResponseTransformer(
    business_date=date.fromisoformat,
)

calendar_service_transformer = ResponseTransformer(
    opens_at=datetime.fromisoformat,
    closes_at=datetime.fromisoformat,
)

availability_service_transformer = ResponseTransformer(
    business_date=date.fromisoformat,
    opens_at=datetime.fromisoformat,
    closes_at=datetime.fromisoformat,
)

availability_slot_transformer = ResponseTransformer(
    slot_at=datetime.fromisoformat,
)


async def reservation_calendar(params: dict[str, Any]) -> list[dict[str, Any]]:
    """Per-day, per-service occupancy of a venue over a date window (the month-grid summary)."""
    response = await reservation_client.client.get(url="reservations/calendar", params=params)
    days = response.json()["days"]
    for day in days:
        calendar_day_transformer.transform(day)
        for service in day["services"]:
            calendar_service_transformer.transform(service)
    return days


async def reservation_availability(params: dict[str, Any]) -> dict[str, Any]:
    """Bookable slots at a venue on one date, for a given party size."""
    response = await reservation_client.client.get(url="reservations/availabilities", params=params)
    availability = response.json()
    availability["business_date"] = date.fromisoformat(availability["business_date"])
    for service in availability["services"]:
        availability_service_transformer.transform(service)
        for slot in service["slots"]:
            availability_slot_transformer.transform(slot)
    return availability

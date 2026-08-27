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

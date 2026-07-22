from uuid import UUID

from ristops_be_venue.services.http import reservation_client


async def has_active_service(venue_id: UUID) -> bool:
    """Return True if the venue has at least one (non-deleted) service configured.

    Reuses be-reservation's existing service search endpoint rather than adding a
    dedicated "exists" endpoint — the list is unpaginated and small per venue, so
    checking for a non-empty result is cheap.
    """
    response = await reservation_client.client.get(
        url="services",
        params={"filter.venue_id": str(venue_id)},
    )
    return len(response.json()["services"]) > 0

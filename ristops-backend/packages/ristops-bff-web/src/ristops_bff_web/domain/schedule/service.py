from datetime import date, datetime, time
from typing import Any
from uuid import UUID

from ristops_bff_web.http import reservation_client
from ristops_lib_core.http import ResponseTransformer

opening_transformer = ResponseTransformer(
    start_time=time.fromisoformat,
    end_time=time.fromisoformat,
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
)

override_transformer = ResponseTransformer(
    date_start=date.fromisoformat,
    date_end=date.fromisoformat,
    start_time=time.fromisoformat,
    end_time=time.fromisoformat,
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
)

service_closing_transformer = ResponseTransformer(
    date_start=date.fromisoformat,
    date_end=date.fromisoformat,
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
)

capacity_override_transformer = ResponseTransformer(
    date_start=date.fromisoformat,
    date_end=date.fromisoformat,
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
)

conflict_transformer = ResponseTransformer(
    conflicting_date_start=date.fromisoformat,
    conflicting_date_end=date.fromisoformat,
    conflicting_start_time=time.fromisoformat,
    conflicting_end_time=time.fromisoformat,
)


async def _get_conflicts(url: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    """GET a `.../conflicts` preview endpoint and return the transformed conflict rows."""
    response = await reservation_client.client.get(url=url, params=params)
    conflicts = response.json()["conflicts"]
    return [conflict_transformer.transform(item) for item in conflicts]


async def list_service_openings(
        service_id: str | UUID,
        include_deleted: bool | None = None,
) -> list[dict[str, Any]]:
    """Return the weekly openings configured for a service."""
    params: dict[str, Any] = {}
    if include_deleted is not None:
        params["include_deleted"] = include_deleted
    response = await reservation_client.client.get(
        url=f"services/{service_id}/openings",
        params=params,
    )
    openings = response.json()["openings"]
    return [opening_transformer.transform(item) for item in openings]


async def upsert_service_openings(
        service_id: str | UUID,
        openings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Replace the full set of weekly openings for a service and return the result."""
    response = await reservation_client.client.put(
        url=f"services/{service_id}/openings",
        json={"openings": openings},
    )
    openings_ = response.json()["openings"]
    return [opening_transformer.transform(item) for item in openings_]



async def search_service_opening_overrides(
        service_id: str | UUID,
        params: dict[str, Any],
) -> dict[str, Any]:
    """Return a page of opening overrides for a service, filtered by the given params."""
    response = await reservation_client.client.get(
        url=f"services/{service_id}/opening-overrides",
        params=params,
    )
    page = response.json()
    page["items"] = [override_transformer.transform(item) for item in page["items"]]
    return page


async def create_service_opening_overrides(
        service_id: str | UUID,
        payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create one or more opening overrides for a service (bulk: one row per weekday)."""
    response = await reservation_client.client.post(
        url=f"services/{service_id}/opening-overrides",
        json=payload,
    )
    return [override_transformer.transform(item) for item in response.json()]


async def update_service_opening_override(
        service_id: str | UUID,
        override_id: str | UUID,
        payload: dict[str, Any],
) -> dict[str, Any]:
    """Update an opening override."""
    response = await reservation_client.client.patch(
        url=f"services/{service_id}/opening-overrides/{override_id}",
        json=payload,
    )
    return override_transformer.get_json(response)


async def delete_service_opening_override(
        service_id: str | UUID,
        override_id: str | UUID,
) -> None:
    """Delete an opening override."""
    await reservation_client.client.delete(
        url=f"services/{service_id}/opening-overrides/{override_id}",
    )


async def service_opening_conflicts(
        service_id: str | UUID,
        params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preview which other services of the venue a candidate weekly opening would overlap."""
    return await _get_conflicts(f"services/{service_id}/openings/conflicts", params)


async def service_opening_override_conflicts(
        service_id: str | UUID,
        params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preview which existing opening overrides a candidate period+weekdays would conflict with,
    plus any cross-service opening overlaps."""
    return await _get_conflicts(f"services/{service_id}/opening-overrides/conflicts", params)



async def search_service_closings(
        service_id: str | UUID,
        params: dict[str, Any],
) -> dict[str, Any]:
    """Return a page of closings for a service, filtered by the given params."""
    response = await reservation_client.client.get(
        url=f"services/{service_id}/closings",
        params=params,
    )
    page = response.json()
    page["items"] = [service_closing_transformer.transform(item) for item in page["items"]]
    return page


async def create_service_closings(
        service_id: str | UUID,
        payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create one or more closings for a service (bulk: one row per weekday)."""
    response = await reservation_client.client.post(
        url=f"services/{service_id}/closings",
        json=payload,
    )
    return [service_closing_transformer.transform(item) for item in response.json()]


async def update_service_closing(
        service_id: str | UUID,
        closing_id: str | UUID,
        payload: dict[str, Any],
) -> dict[str, Any]:
    """Update a closing."""
    response = await reservation_client.client.patch(
        url=f"services/{service_id}/closings/{closing_id}",
        json=payload,
    )
    return service_closing_transformer.get_json(response)


async def delete_service_closing(
        service_id: str | UUID,
        closing_id: str | UUID,
) -> None:
    """Delete a closing."""
    await reservation_client.client.delete(
        url=f"services/{service_id}/closings/{closing_id}",
    )


async def service_closing_conflicts(
        service_id: str | UUID,
        params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preview which existing service closings (this service) or venue closings (its venue) a
    candidate period+weekdays would conflict with."""
    return await _get_conflicts(f"services/{service_id}/closings/conflicts", params)



async def search_service_capacity_overrides(
        service_id: str | UUID,
        params: dict[str, Any],
) -> dict[str, Any]:
    """Return a page of capacity overrides for a service, filtered by the given params."""
    response = await reservation_client.client.get(
        url=f"services/{service_id}/capacity-overrides",
        params=params,
    )
    page = response.json()
    page["items"] = [capacity_override_transformer.transform(item) for item in page["items"]]
    return page


async def create_service_capacity_overrides(
        service_id: str | UUID,
        payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create one or more capacity overrides for a service (bulk: one row per weekday)."""
    response = await reservation_client.client.post(
        url=f"services/{service_id}/capacity-overrides",
        json=payload,
    )
    return [capacity_override_transformer.transform(item) for item in response.json()]


async def update_service_capacity_override(
        service_id: str | UUID,
        capacity_override_id: str | UUID,
        payload: dict[str, Any],
) -> dict[str, Any]:
    """Update a capacity override."""
    response = await reservation_client.client.patch(
        url=f"services/{service_id}/capacity-overrides/{capacity_override_id}",
        json=payload,
    )
    return capacity_override_transformer.get_json(response)


async def delete_service_capacity_override(
        service_id: str | UUID,
        capacity_override_id: str | UUID,
) -> None:
    """Delete a capacity override."""
    await reservation_client.client.delete(
        url=f"services/{service_id}/capacity-overrides/{capacity_override_id}",
    )


async def service_capacity_override_conflicts(
        service_id: str | UUID,
        params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preview which existing capacity overrides a candidate period+weekdays would conflict with."""
    return await _get_conflicts(f"services/{service_id}/capacity-overrides/conflicts", params)



venue_closing_transformer = ResponseTransformer(
    date_start=date.fromisoformat,
    date_end=date.fromisoformat,
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
)


async def search_venue_closings(
        venue_id: str | UUID,
        params: dict[str, Any],
) -> dict[str, Any]:
    """Return a page of venue-wide closings for a venue, filtered by the given params."""
    response = await reservation_client.client.get(
        url=f"venues/{venue_id}/closings",
        params=params,
    )
    page = response.json()
    page["items"] = [venue_closing_transformer.transform(item) for item in page["items"]]
    return page


async def create_venue_closings(
        venue_id: str | UUID,
        payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create one or more venue-wide closings (bulk: one row per weekday)."""
    response = await reservation_client.client.post(
        url=f"venues/{venue_id}/closings",
        json=payload,
    )
    return [venue_closing_transformer.transform(item) for item in response.json()]


async def update_venue_closing(
        venue_id: str | UUID,
        closing_id: str | UUID,
        payload: dict[str, Any],
) -> dict[str, Any]:
    """Update a venue-wide closing."""
    response = await reservation_client.client.patch(
        url=f"venues/{venue_id}/closings/{closing_id}",
        json=payload,
    )
    return venue_closing_transformer.get_json(response)


async def delete_venue_closing(
        venue_id: str | UUID,
        closing_id: str | UUID,
) -> None:
    """Delete a venue-wide closing."""
    await reservation_client.client.delete(
        url=f"venues/{venue_id}/closings/{closing_id}",
    )


async def venue_closing_conflicts(
        venue_id: str | UUID,
        params: dict[str, Any],
) -> list[dict[str, Any]]:
    """Preview which existing venue closings a candidate period+weekdays would conflict with."""
    return await _get_conflicts(f"venues/{venue_id}/closings/conflicts", params)

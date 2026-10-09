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

closing_transformer = ResponseTransformer(
    date_from=date.fromisoformat,
    date_to=date.fromisoformat,
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
)


async def list_service_openings(
        service_id: str | UUID,
        include_deleted: bool | None = None,
) -> list[dict[str, Any]]:
    """Return a service's weekly opening hours."""
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
        payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Replace a service's weekly opening hours with the submitted set."""
    response = await reservation_client.client.put(
        url=f"services/{service_id}/openings",
        json=payload,
    )
    openings = response.json()["openings"]
    return [opening_transformer.transform(item) for item in openings]


async def search_closings(
        venue_id: str | UUID,
        params: dict[str, Any],
) -> dict[str, Any]:
    """Return a page of the venue's closings, filtered by the given params."""
    response = await reservation_client.client.get(
        url=f"venues/{venue_id}/closings",
        params=params,
    )
    page = response.json()
    page["items"] = [closing_transformer.transform(item) for item in page["items"]]
    return page


async def create_closing(venue_id: str | UUID, payload: dict[str, Any]) -> dict[str, Any]:
    """Close one or more of the venue's services over a date range."""
    response = await reservation_client.client.post(
        url=f"venues/{venue_id}/closings",
        json=payload,
    )
    return closing_transformer.get_json(response)


async def update_closing(
        venue_id: str | UUID,
        closing_id: str | UUID,
        payload: dict[str, Any],
) -> dict[str, Any]:
    """Update a closing's period, services or description."""
    response = await reservation_client.client.patch(
        url=f"venues/{venue_id}/closings/{closing_id}",
        json=payload,
    )
    return closing_transformer.get_json(response)


async def delete_closing(venue_id: str | UUID, closing_id: str | UUID) -> None:
    """Delete a closing."""
    await reservation_client.client.delete(
        url=f"venues/{venue_id}/closings/{closing_id}",
    )

from datetime import datetime
from typing import Any
from uuid import UUID

from ristops_bff_web.http import venue_client
from ristops_lib_core.http import ResponseTransformer

venue_transformer = ResponseTransformer(
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
)

role_transformer = ResponseTransformer()


async def search_venues(params: dict[str, Any]) -> dict[str, Any]:
    response = await venue_client.client.get(
        url="venues",
        params=params,
    )
    page = response.json()
    page["items"] = [venue_transformer.transform(item) for item in page["items"]]
    return page


async def find_venue(venue_id: str | UUID) -> dict[str, Any]:
    response = await venue_client.client.get(
        url=f"venues/{venue_id}",
    )
    return venue_transformer.get_json(response)


async def create_venue(create_venue_input: dict[str, Any]) -> dict[str, Any]:
    response = await venue_client.client.post(
        url=f"venues",
        json=create_venue_input,
    )
    return venue_transformer.get_json(response)


async def update_venue(venue_id: str | UUID, update_venue_input: dict[str, Any]) -> dict[str, Any]:
    response = await venue_client.client.patch(
        url=f"venues/{venue_id}",
        json=update_venue_input,
    )
    return venue_transformer.get_json(response)


async def perform_venue_action(venue_id: str | UUID, action_type: str) -> dict[str, Any]:
    """Perform a lifecycle action (activate/close/disable/enable) on a venue."""
    response = await venue_client.client.post(
        url=f"venues/{venue_id}/actions",
        json={"action_type": action_type},
    )
    return venue_transformer.get_json(response)

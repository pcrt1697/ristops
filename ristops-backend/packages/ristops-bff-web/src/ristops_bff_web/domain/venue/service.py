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

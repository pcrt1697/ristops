from datetime import date, datetime
from typing import Any
from uuid import UUID

from ristops_bff_web.http import reservation_client
from ristops_lib_core.http import ResponseTransformer

service_transformer = ResponseTransformer(
    date_from=date.fromisoformat,
    date_to=date.fromisoformat,
    created_at=datetime.fromisoformat,
    updated_at=datetime.fromisoformat,
    deleted_at=datetime.fromisoformat,
)


async def list_services(
        venue_id: str | UUID,
        name: str | None = None,
        include_deleted: bool | None = None,
) -> list[dict[str, Any]]:
    params: dict[str, Any] = {"filter.venue_id": str(venue_id)}
    if name is not None:
        params["filter.name"] = name
    if include_deleted is not None:
        params["filter.include_deleted"] = include_deleted
    response = await reservation_client.client.get(
        url="services",
        params=params,
    )
    services = response.json()["services"]
    return [service_transformer.transform(item) for item in services]


async def find_service(service_id: str | UUID) -> dict[str, Any]:
    response = await reservation_client.client.get(
        url=f"services/{service_id}",
    )
    return service_transformer.get_json(response)


async def create_service(create_service_input: dict[str, Any]) -> dict[str, Any]:
    response = await reservation_client.client.post(
        url="services",
        json=create_service_input,
    )
    return service_transformer.get_json(response)


async def update_service(service_id: str | UUID, update_service_input: dict[str, Any]) -> dict[str, Any]:
    response = await reservation_client.client.patch(
        url=f"services/{service_id}",
        json=update_service_input,
    )
    return service_transformer.get_json(response)


async def delete_service(service_id: str | UUID) -> None:
    await reservation_client.client.delete(
        url=f"services/{service_id}",
    )

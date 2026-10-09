from builtins import list
from datetime import date, datetime
from typing import Annotated, Any

import strawberry

from ristops_bff_web.domain.service.service import (
    find_service, create_service, update_service, delete_service, list_services,
)
from ristops_bff_web.domain.venue.graphql import Venue, resolve_venue
from ristops_bff_web.graphql.types import EntityId


def _create_payload(inp: "CreateServiceInput") -> dict[str, Any]:
    return {
        "venue_id": inp.venue_id,
        "name": inp.name,
        "description": inp.description,
        "date_from": inp.date_from.isoformat(),
        "date_to": inp.date_to.isoformat() if inp.date_to is not None else None,
        "capacity": inp.capacity,
    }


def _update_payload(inp: "UpdateServiceInput") -> dict[str, Any]:
    """Send only provided fields, so unset ones aren't touched. ``date_to`` defaults to UNSET, so
    an explicit null is forwarded and re-opens the service indefinitely, while an omitted one
    leaves the current end date alone."""
    payload: dict[str, Any] = {}
    if inp.name is not None:
        payload["name"] = inp.name
    if inp.description is not strawberry.UNSET:
        payload["description"] = inp.description
    if inp.date_from is not None:
        payload["date_from"] = inp.date_from.isoformat()
    if inp.date_to is not strawberry.UNSET:
        payload["date_to"] = inp.date_to.isoformat() if inp.date_to is not None else None
    if inp.capacity is not None:
        payload["capacity"] = inp.capacity
    return payload


async def resolve_get_service(
        service_id: EntityId
) -> "Service":
    service = await find_service(service_id)
    return Service.from_dict(service)


async def resolve_create_service(
        _input: Annotated[
            "CreateServiceInput",
            strawberry.argument(description="Service information.", name="input")
        ]
) -> "Service":
    service = await create_service(_create_payload(_input))
    return Service.from_dict(service)


async def resolve_update_service(
        service_id: EntityId,
        _input: Annotated[
            "UpdateServiceInput",
            strawberry.argument(description="Service information to update.", name="input")
        ]
) -> "Service":
    service = await update_service(service_id, _update_payload(_input))
    return Service.from_dict(service)


async def resolve_delete_service(
        service_id: EntityId
) -> bool:
    """Delete a service by ID. Returns True when the deletion succeeds."""
    await delete_service(service_id)
    return True


async def resolve_list_services(
        venue_id: Annotated[
            strawberry.ID,
            strawberry.argument(description="Venue ID to list services for.")
        ],
        name: Annotated[
            str | None,
            strawberry.argument(description="Filter by service name using a like operator.")
        ] = None,
        include_deleted: Annotated[
            bool | None,
            strawberry.argument(description="Include deleted services.")
        ] = None,
) -> list["Service"]:
    services = await list_services(venue_id, name, include_deleted)
    return [Service.from_dict(service) for service in services]


@strawberry.type(
    description="Service entity information.",
)
class Service:
    venue_id: strawberry.Private[str]
    id: str = strawberry.field(
        description="Service identifier.",
    )
    name: str = strawberry.field(
        description="Name of the service.",
    )
    description: str | None = strawberry.field(
        description="Description of the service.",
    )
    date_from: date = strawberry.field(
        description="First date the service runs on (inclusive).",
    )
    date_to: date | None = strawberry.field(
        description="Last date the service runs on (inclusive); null runs it indefinitely.",
    )
    capacity: int = strawberry.field(
        description="Maximum number of seats bookable on any date the service runs.",
    )
    deleted_at: datetime | None = strawberry.field(
        description="Deletion date, if the service has been deleted.",
    )
    created_at: datetime = strawberry.field(
        description="Creation date.",
    )
    updated_at: datetime = strawberry.field(
        description="Last update date.",
    )
    venue: Venue = strawberry.field(
        description="Venue this service belongs to.",
        resolver=resolve_venue,
    )

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "Service":
        return Service(
            id=obj["id"],
            venue_id=obj["venue_id"],
            name=obj["name"],
            description=obj.get("description"),
            date_from=obj["date_from"],
            date_to=obj.get("date_to"),
            capacity=obj["capacity"],
            deleted_at=obj.get("deleted_at"),
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


@strawberry.input(
    description="Service information.",
)
class CreateServiceInput:
    venue_id: str = strawberry.field(
        description="Identifier of the venue this service belongs to.",
    )
    name: str = strawberry.field(
        description="Name of the service.",
    )
    date_from: date = strawberry.field(
        description="First date the service runs on (inclusive).",
    )
    capacity: int = strawberry.field(
        description="Maximum number of seats bookable on any date the service runs.",
    )
    description: str | None = strawberry.field(
        default=None,
        description="Description of the service.",
    )
    date_to: date | None = strawberry.field(
        default=None,
        description="Last date the service runs on (inclusive). Omit to run it indefinitely; "
                    "set it equal to dateFrom for a one-shot service.",
    )


@strawberry.input(
    description="Service information to update.",
)
class UpdateServiceInput:
    name: str | None = strawberry.field(
        default=None,
        description="New name of the service.",
    )
    date_from: date | None = strawberry.field(
        default=None,
        description="New first date the service runs on (inclusive).",
    )
    capacity: int | None = strawberry.field(
        default=None,
        description="New maximum number of seats bookable on any date the service runs.",
    )
    # UNSET default so an omitted field is left unchanged while an explicit null clears it — the
    # two fields the backend allows clearing. (name/dateFrom/capacity can't be cleared, so a
    # plain None default is fine there.)
    description: str | None = strawberry.field(
        default=strawberry.UNSET,
        description="New description of the service (null clears it).",
    )
    date_to: date | None = strawberry.field(
        default=strawberry.UNSET,
        description="New last date the service runs on (null runs it indefinitely).",
    )


@strawberry.type
class ServiceQuery:
    service: Service = strawberry.field(
        resolver=resolve_get_service,
        description="Fetch service by ID",
    )
    listServices: list[Service] = strawberry.field(
        resolver=resolve_list_services,
        description="List services for a venue.",
    )


@strawberry.type
class ServiceMutation:
    create_service = strawberry.mutation(
        resolver=resolve_create_service,
        description="Create a new service.",
    )
    update_service = strawberry.mutation(
        resolver=resolve_update_service,
        description="Update a service.",
    )
    delete_service = strawberry.mutation(
        resolver=resolve_delete_service,
        description="Delete a service.",
    )

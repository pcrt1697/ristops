from builtins import list
from datetime import datetime
from typing import Annotated, Any

import strawberry

from ristops_bff_web.domain.service.service import (
    find_service, create_service, update_service, delete_service, list_services,
)
from ristops_bff_web.domain.venue.graphql import Venue, resolve_venue
from ristops_bff_web.graphql.types import EntityId


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
    service = await create_service(strawberry.asdict(_input))
    return Service.from_dict(service)


async def resolve_update_service(
        service_id: EntityId,
        _input: Annotated[
            "UpdateServiceInput",
            strawberry.argument(description="Service information to update.", name="input")
        ]
) -> "Service":
    service = await update_service(service_id, strawberry.asdict(_input))
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
    turn_time_m: int = strawberry.field(
        description="Reservation duration, in minutes.",
    )
    advance_notice_m: int = strawberry.field(
        description="Minimum notice required before a reservation slot, in minutes.",
    )
    slot_interval_m: int = strawberry.field(
        description="Interval between reservation slots, in minutes.",
    )
    grace_period_m: int = strawberry.field(
        description="Minutes past a reservation's start time before it may be marked as a no-show.",
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
            turn_time_m=obj["turn_time_m"],
            advance_notice_m=obj["advance_notice_m"],
            slot_interval_m=obj["slot_interval_m"],
            grace_period_m=obj["grace_period_m"],
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
    description: str | None = strawberry.field(
        default=None,
        description="Description of the service.",
    )
    turn_time_m: int = strawberry.field(
        description="Reservation duration, in minutes.",
    )
    advance_notice_m: int = strawberry.field(
        description="Minimum notice required before a reservation slot, in minutes.",
    )
    slot_interval_m: int = strawberry.field(
        description="Interval between reservation slots, in minutes.",
    )
    grace_period_m: int = strawberry.field(
        description="Minutes past a reservation's start time before it may be marked as a no-show.",
    )


@strawberry.input(
    description="Service information to update.",
)
class UpdateServiceInput:
    name: str | None = strawberry.field(
        default=None,
        description="New name of the service.",
    )
    description: str | None = strawberry.field(
        default=None,
        description="New description of the service.",
    )
    turn_time_m: int | None = strawberry.field(
        default=None,
        description="New reservation duration, in minutes.",
    )
    advance_notice_m: int | None = strawberry.field(
        default=None,
        description="New minimum notice required before a reservation slot, in minutes.",
    )
    slot_interval_m: int | None = strawberry.field(
        default=None,
        description="New interval between reservation slots, in minutes.",
    )
    grace_period_m: int | None = strawberry.field(
        default=None,
        description="New minutes past a reservation's start time before it may be marked as a no-show.",
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

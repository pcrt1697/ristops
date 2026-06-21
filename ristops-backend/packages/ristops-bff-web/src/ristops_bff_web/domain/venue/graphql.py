from datetime import datetime
from typing import Annotated
from typing import Any

import strawberry

from ristops_bff_web.domain.venue.service import find_venue, create_venue, update_venue
from ristops_bff_web.graphql.types import EntityId


async def resolve_get_venue(
        venue_id: EntityId
) -> Venue:
    venue = await find_venue(venue_id)
    return Venue.from_dict(venue)


async def resolve_create_venue(
        _input: Annotated[
            CreateVenueInput,
            strawberry.argument(description="Venue information.", name="input")
        ]
) -> Venue:
    venue = await create_venue(strawberry.asdict(_input))
    return Venue.from_dict(venue)


async def resolve_update_venue(
        venue_id: EntityId,
        _input: Annotated[
            UpdateVenueInput,
            strawberry.argument(description="Venue information to update.", name="input")
        ]
) -> Venue:
    venue = await update_venue(venue_id, strawberry.asdict(_input))
    return Venue.from_dict(venue)


@strawberry.type(
    description="Venue entity information.",
)
class Venue:
    id: str = strawberry.field(
        description="Venue identifier.",
    )
    name: str = strawberry.field(
        description="Name of the venue.",
    )
    address: str = strawberry.field(
        description="Address of the venue.",
    )
    description: str | None = strawberry.field(
        description="Description of the venue.",
    )
    created_at: datetime = strawberry.field(
        description="Creation date.",
    )
    updated_at: datetime = strawberry.field(
        description="Last update date.",
    )

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "Venue":
        return Venue(
            id=obj["id"],
            name=obj["name"],
            address=obj["address"],
            description=obj.get("description"),
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


@strawberry.input(
    description="Venue information.",
)
class CreateVenueInput:
    name: str = strawberry.field(
        description="Name of the venue.",
    )
    address: str = strawberry.field(
        description="Address of the venue.",
    )
    description: str | None = strawberry.field(
        description="Description of the venue.",
    )


@strawberry.input(
    description="Venue information to update.",
)
class UpdateVenueInput:
    name: str | None = strawberry.field(
        default=None,
        description="New name of the venue.",
    )
    address: str | None = strawberry.field(
        default=None,
        description="New address of the user.",
    )
    description: str | None = strawberry.field(
        default=None,
        description="New description of the venue.",
    )


@strawberry.type
class VenueQuery:
    venue: Venue = strawberry.field(
        resolver=resolve_get_venue,
        description="Fetch venue by ID",
    )
    # todo: add my venues


@strawberry.type
class VenueMutation:
    create_venue = strawberry.mutation(
        resolver=resolve_create_venue,
        description="Create a new venue.",
    )
    update_venue = strawberry.mutation(
        resolver=resolve_update_venue,
        description="Update venue data",
    )

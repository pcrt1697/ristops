from datetime import datetime
from enum import Enum
from typing import Annotated
from typing import Any

import strawberry

from ristops_bff_web.domain.venue.service import find_venue, create_venue, update_venue, search_venues
from ristops_bff_web.graphql.pagination import Page, PaginationInput, SearchQueryParams, SortInput
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


async def resolve_search_venues(
        _input: Annotated[
            "VenueSearchInput",
            strawberry.argument(description="Venue search query.", name="input")
        ]
) -> Page["Venue"]:
    params = VenueQueryParams(_input).build()
    page = await search_venues(params)
    return Page.from_dict(page, Venue.from_dict)


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
        default=None,
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
        description="New address of the venue.",
    )
    description: str | None = strawberry.field(
        default=None,
        description="New description of the venue.",
    )


@strawberry.input(
    description="Venue search filter.",
)
class VenueFilterInput:
    name: str | None = strawberry.field(
        default=None,
        description="Filter by venue name using `like` operator.",
    )


@strawberry.enum(description="Fields a venue search may be sorted by.")
class VenueSortField(Enum):
    NAME = "name"
    ID = "id"
    CREATED_AT = "created_at"


@strawberry.input(description="Venue search query.")
class VenueSearchInput:
    pagination: PaginationInput = strawberry.field(
        default_factory=PaginationInput,
        description="Pagination parameters.",
    )
    sort: list[SortInput[VenueSortField]] = strawberry.field(
        default_factory=list,
        description="Sort instructions.",
    )
    filter: VenueFilterInput | None = strawberry.field(
        default=None,
        description="Filter parameters.",
    )


class VenueQueryParams(SearchQueryParams):
    """Builds the backend venue-search query params from a VenueSearchInput."""

    def __init__(self, search: VenueSearchInput) -> None:
        super().__init__(search.pagination, search.sort)
        self._filter = search.filter

    def _finalize(self) -> None:
        if self._filter is not None:
            self._set_filter("name", self._filter.name)


@strawberry.type
class VenueQuery:
    venue: Venue = strawberry.field(
        resolver=resolve_get_venue,
        description="Fetch venue by ID",
    )
    searchVenues: Page[Venue] = strawberry.field(
        resolver=resolve_search_venues,
        description="Search venues the user has access to.",
    )


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

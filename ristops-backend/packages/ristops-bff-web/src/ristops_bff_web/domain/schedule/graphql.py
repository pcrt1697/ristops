from datetime import date, datetime, time
from enum import Enum
from typing import Annotated, Any

import strawberry

from ristops_bff_web.domain.schedule.service import (
    create_closing, delete_closing, list_service_openings, search_closings, update_closing,
    upsert_service_openings,
)
from ristops_bff_web.graphql.pagination import Page, PaginationInput, SearchQueryParams, SortInput
from ristops_bff_web.graphql.types import EntityId


@strawberry.enum(description="Day of the week an opening applies to.")
class Weekday(Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


@strawberry.type(description="A service's opening hours on one weekday.")
class Opening:
    id: str = strawberry.field(description="Opening identifier.")
    service_id: str = strawberry.field(description="Service this opening belongs to.")
    weekday: Weekday = strawberry.field(description="Day of the week this opening applies to.")
    start_time: time = strawberry.field(description="Time the service opens.")
    end_time: time = strawberry.field(
        description="Time the service closes. An end at or before the start runs overnight, "
                    "closing on the following day.",
    )
    description: str | None = strawberry.field(description="Description of this opening.")
    created_at: datetime = strawberry.field(description="Creation date.")
    updated_at: datetime = strawberry.field(description="Last update date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "Opening":
        return Opening(
            id=obj["id"],
            service_id=obj["service_id"],
            weekday=Weekday(obj["weekday"]),
            start_time=obj["start_time"],
            end_time=obj["end_time"],
            description=obj.get("description"),
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


@strawberry.input(description="One weekday's opening hours within an openings upsert.")
class OpeningUpsertInput:
    weekday: Weekday = strawberry.field(description="Day of the week this opening applies to.")
    start_time: time = strawberry.field(description="Time the service opens.")
    end_time: time = strawberry.field(description="Time the service closes.")
    description: str | None = strawberry.field(
        default=None, description="Description of this opening.",
    )


@strawberry.type(description="A date range over which the linked services do not run.")
class Closing:
    id: str = strawberry.field(description="Closing identifier.")
    venue_id: str = strawberry.field(description="Venue this closing belongs to.")
    date_from: date = strawberry.field(description="First date of the closing period (inclusive).")
    date_to: date = strawberry.field(description="Last date of the closing period (inclusive).")
    service_ids: list[str] = strawberry.field(description="Services this closing applies to.")
    description: str | None = strawberry.field(description="Description of this closing.")
    created_at: datetime = strawberry.field(description="Creation date.")
    updated_at: datetime = strawberry.field(description="Last update date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "Closing":
        return Closing(
            id=obj["id"],
            venue_id=obj["venue_id"],
            date_from=obj["date_from"],
            date_to=obj["date_to"],
            service_ids=obj.get("service_ids", []),
            description=obj.get("description"),
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


@strawberry.input(description="Information to create a closing.")
class ClosingCreateInput:
    date_from: date = strawberry.field(description="First date of the closing period (inclusive).")
    date_to: date = strawberry.field(description="Last date of the closing period (inclusive).")
    service_ids: list[strawberry.ID] = strawberry.field(
        description="Services this closing applies to. Pass every service of the venue for a "
                    "venue-wide shutdown.",
    )
    description: str | None = strawberry.field(
        default=None, description="Description of this closing.",
    )


@strawberry.input(description="Closing fields to update (only provided fields change).")
class ClosingUpdateInput:
    date_from: date | None = strawberry.field(
        default=None, description="New first date of the closing period (inclusive).",
    )
    date_to: date | None = strawberry.field(
        default=None, description="New last date of the closing period (inclusive).",
    )
    service_ids: list[strawberry.ID] | None = strawberry.field(
        default=None, description="New complete set of services this closing applies to.",
    )
    description: str | None = strawberry.field(
        default=strawberry.UNSET, description="New description (null clears it).",
    )


@strawberry.enum(description="Fields a closing search may be sorted by.")
class ClosingSortField(Enum):
    DATE_FROM = "date_from"
    DATE_TO = "date_to"
    CREATED_AT = "created_at"
    ID = "id"


@strawberry.input(description="Closing search filter.")
class ClosingFilterInput:
    date_from: date | None = strawberry.field(
        default=None, description="Include closings ending on or after this date.",
    )
    date_to: date | None = strawberry.field(
        default=None, description="Include closings starting on or before this date.",
    )
    service_id: strawberry.ID | None = strawberry.field(
        default=None, description="Return only closings applying to this service.",
    )


@strawberry.input(description="Closing search query.")
class ClosingSearchInput:
    pagination: PaginationInput | None = strawberry.field(
        default=None, description="Pagination parameters.",
    )
    sort: list[SortInput[ClosingSortField]] = strawberry.field(
        default_factory=list, description="Sort instructions.",
    )
    filter: ClosingFilterInput | None = strawberry.field(
        default=None, description="Filter parameters.",
    )


class ClosingQueryParams(SearchQueryParams):
    """Builds the backend closing-search query params from a ClosingSearchInput."""

    def __init__(self, search: ClosingSearchInput) -> None:
        super().__init__(search.pagination or PaginationInput(), search.sort)
        self._filter = search.filter

    def _finalize(self) -> None:
        if self._filter is None:
            return
        if self._filter.date_from is not None:
            self._set_filter("date_from", self._filter.date_from.isoformat())
        if self._filter.date_to is not None:
            self._set_filter("date_to", self._filter.date_to.isoformat())
        if self._filter.service_id is not None:
            self._set_filter("service_id", str(self._filter.service_id))


def _closing_create_payload(inp: ClosingCreateInput) -> dict[str, Any]:
    return {
        "date_from": inp.date_from.isoformat(),
        "date_to": inp.date_to.isoformat(),
        "service_ids": [str(service_id) for service_id in inp.service_ids],
        "description": inp.description,
    }


def _closing_update_payload(inp: ClosingUpdateInput) -> dict[str, Any]:
    """Send only provided fields, so unset ones aren't touched."""
    payload: dict[str, Any] = {}
    if inp.date_from is not None:
        payload["date_from"] = inp.date_from.isoformat()
    if inp.date_to is not None:
        payload["date_to"] = inp.date_to.isoformat()
    if inp.service_ids is not None:
        payload["service_ids"] = [str(service_id) for service_id in inp.service_ids]
    if inp.description is not strawberry.UNSET:
        payload["description"] = inp.description
    return payload


async def resolve_service_openings(
        service_id: Annotated[strawberry.ID, strawberry.argument(description="Service ID.")],
        include_deleted: Annotated[
            bool | None,
            strawberry.argument(description="Return the openings even if the service is deleted."),
        ] = None,
) -> list[Opening]:
    openings = await list_service_openings(service_id, include_deleted)
    return [Opening.from_dict(opening) for opening in openings]


async def resolve_upsert_service_openings(
        service_id: Annotated[strawberry.ID, strawberry.argument(description="Service ID.")],
        _input: Annotated[
            list[OpeningUpsertInput],
            strawberry.argument(description="The service's complete weekly hours.", name="input"),
        ],
) -> list[Opening]:
    payload = {
        "openings": [
            {
                "weekday": item.weekday.value,
                "start_time": item.start_time.isoformat(),
                "end_time": item.end_time.isoformat(),
                "description": item.description,
            }
            for item in _input
        ],
    }
    openings = await upsert_service_openings(service_id, payload)
    return [Opening.from_dict(opening) for opening in openings]


async def resolve_venue_closings(
        venue_id: EntityId,
        _input: Annotated[
            ClosingSearchInput | None,
            strawberry.argument(description="Closing search query.", name="input")
        ] = None,
) -> Page[Closing]:
    search = _input or ClosingSearchInput()
    params = ClosingQueryParams(search).build()
    page = await search_closings(venue_id, params)
    return Page.from_dict(page, Closing.from_dict)


async def resolve_create_closing(
        venue_id: EntityId,
        _input: Annotated[
            ClosingCreateInput,
            strawberry.argument(description="Closing information.", name="input")
        ],
) -> Closing:
    return Closing.from_dict(await create_closing(venue_id, _closing_create_payload(_input)))


async def resolve_update_closing(
        venue_id: EntityId,
        closing_id: Annotated[strawberry.ID, strawberry.argument(description="Closing ID.")],
        _input: Annotated[
            ClosingUpdateInput,
            strawberry.argument(description="Closing fields to update.", name="input")
        ],
) -> Closing:
    return Closing.from_dict(
        await update_closing(venue_id, closing_id, _closing_update_payload(_input))
    )


async def resolve_delete_closing(
        venue_id: EntityId,
        closing_id: Annotated[strawberry.ID, strawberry.argument(description="Closing ID.")],
) -> bool:
    """Delete a closing. Returns True when the deletion succeeds."""
    await delete_closing(venue_id, closing_id)
    return True


@strawberry.type
class ScheduleQuery:
    service_openings: list[Opening] = strawberry.field(
        resolver=resolve_service_openings,
        description="A service's weekly opening hours.",
    )
    venue_closings: Page[Closing] = strawberry.field(
        resolver=resolve_venue_closings,
        description="Search a venue's closings.",
    )


@strawberry.type
class ScheduleMutation:
    upsert_service_openings = strawberry.mutation(
        resolver=resolve_upsert_service_openings,
        description="Replace a service's weekly opening hours.",
    )
    create_closing = strawberry.mutation(
        resolver=resolve_create_closing,
        description="Close one or more of a venue's services over a date range.",
    )
    update_closing = strawberry.mutation(
        resolver=resolve_update_closing,
        description="Update a closing.",
    )
    delete_closing = strawberry.mutation(
        resolver=resolve_delete_closing,
        description="Delete a closing.",
    )

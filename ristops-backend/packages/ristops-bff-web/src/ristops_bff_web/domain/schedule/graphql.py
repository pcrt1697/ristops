from builtins import list
from datetime import date, datetime, time
from enum import Enum
from typing import Annotated, Any

import strawberry

from ristops_bff_web.domain.schedule.service import (
    list_service_openings, upsert_service_openings,
    search_service_opening_overrides, create_service_opening_overrides,
    update_service_opening_override, delete_service_opening_override,
    search_service_closings, create_service_closings,
    update_service_closing, delete_service_closing,
    search_service_capacity_overrides, create_service_capacity_overrides,
    update_service_capacity_override, delete_service_capacity_override,
    search_venue_closings, create_venue_closings,
    update_venue_closing, delete_venue_closing,
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


@strawberry.type(
    description="A service's weekly opening for a given weekday.",
)
class Opening:
    id: str = strawberry.field(description="Opening identifier.")
    service_id: str = strawberry.field(
        description="Identifier of the service this opening belongs to.",
    )
    weekday: Weekday = strawberry.field(description="Day of the week this opening applies to.")
    capacity: int = strawberry.field(description="Maximum number of reservable seats.")
    start_time: time = strawberry.field(description="Time the service opens.")
    end_time: time = strawberry.field(description="Time the service closes.")
    description: str | None = strawberry.field(description="Description of this opening.")
    created_at: datetime = strawberry.field(description="Creation date.")
    updated_at: datetime = strawberry.field(description="Last update date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "Opening":
        return Opening(
            id=obj["id"],
            service_id=obj["service_id"],
            weekday=Weekday(obj["weekday"]),
            capacity=obj["capacity"],
            start_time=obj["start_time"],
            end_time=obj["end_time"],
            description=obj.get("description"),
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


@strawberry.input(
    description="A single weekly opening within a bulk upsert.",
)
class OpeningUpsertInput:
    weekday: Weekday = strawberry.field(description="Day of the week this opening applies to.")
    capacity: int = strawberry.field(description="Maximum number of reservable seats.")
    start_time: time = strawberry.field(description="Time the service opens.")
    end_time: time = strawberry.field(description="Time the service closes.")
    description: str | None = strawberry.field(
        default=None,
        description="Description of this opening.",
    )


async def resolve_service_openings(
        service_id: EntityId,
        include_deleted: Annotated[
            bool | None,
            strawberry.argument(description="Include openings even if the service has been deleted.")
        ] = None,
) -> list[Opening]:
    openings = await list_service_openings(service_id, include_deleted)
    return [Opening.from_dict(opening) for opening in openings]


async def resolve_upsert_service_openings(
        service_id: EntityId,
        openings: Annotated[
            list[OpeningUpsertInput],
            strawberry.argument(description="The complete set of weekly openings to apply.")
        ],
) -> list[Opening]:
    payload = [
        {
            "weekday": opening.weekday.value,
            "capacity": opening.capacity,
            "start_time": opening.start_time.isoformat(),
            "end_time": opening.end_time.isoformat(),
            "description": opening.description,
        }
        for opening in openings
    ]
    result = await upsert_service_openings(service_id, payload)
    return [Opening.from_dict(opening) for opening in result]


@strawberry.type(description="A one-off opening override replacing base hours for a date range.")
class OpeningOverride:
    id: str = strawberry.field(description="Override identifier.")
    service_id: str = strawberry.field(description="Identifier of the service this override belongs to.")
    date_start: date = strawberry.field(description="First date of the override period (inclusive).")
    date_end: date = strawberry.field(description="Last date of the override period (inclusive).")
    weekday: Weekday | None = strawberry.field(
        description="Weekday the override applies to within the range; null means every day.",
    )
    capacity: int = strawberry.field(description="Overridden maximum number of reservable seats.")
    start_time: time = strawberry.field(description="Overridden opening time.")
    end_time: time = strawberry.field(description="Overridden closing time.")
    description: str | None = strawberry.field(description="Description of this override.")
    created_at: datetime = strawberry.field(description="Creation date.")
    updated_at: datetime = strawberry.field(description="Last update date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "OpeningOverride":
        return OpeningOverride(
            id=obj["id"],
            service_id=obj["service_id"],
            date_start=obj["date_start"],
            date_end=obj["date_end"],
            weekday=Weekday(obj["weekday"]) if obj.get("weekday") else None,
            capacity=obj["capacity"],
            start_time=obj["start_time"],
            end_time=obj["end_time"],
            description=obj.get("description"),
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


@strawberry.type(description="A one-off closing for a date range.")
class ServiceClosing:
    id: str = strawberry.field(description="Closing identifier.")
    service_id: str = strawberry.field(description="Identifier of the service this closing belongs to.")
    date_start: date = strawberry.field(description="First date of the closing period (inclusive).")
    date_end: date = strawberry.field(description="Last date of the closing period (inclusive).")
    weekday: Weekday | None = strawberry.field(
        description="Weekday the closing applies to within the range; null means every day.",
    )
    description: str | None = strawberry.field(description="Description of this closing.")
    created_at: datetime = strawberry.field(description="Creation date.")
    updated_at: datetime = strawberry.field(description="Last update date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "ServiceClosing":
        return ServiceClosing(
            id=obj["id"],
            service_id=obj["service_id"],
            date_start=obj["date_start"],
            date_end=obj["date_end"],
            weekday=Weekday(obj["weekday"]) if obj.get("weekday") else None,
            description=obj.get("description"),
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


@strawberry.input(description="New opening override information. Bulk: one row is created per "
                               "weekday in `weekdays`; omitted/empty, or all seven, means every day.")
class OpeningOverrideCreateInput:
    date_start: date = strawberry.field(description="First date of the override period (inclusive).")
    date_end: date = strawberry.field(description="Last date of the override period (inclusive).")
    weekdays: list[Weekday] | None = strawberry.field(
        default=None,
        description="Weekdays to scope to; provide multiple to create one row per weekday.",
    )
    capacity: int = strawberry.field(description="Overridden maximum number of reservable seats.")
    start_time: time = strawberry.field(description="Overridden opening time.")
    end_time: time = strawberry.field(description="Overridden closing time.")
    description: str | None = strawberry.field(default=None, description="Description of this override.")


@strawberry.input(description="Opening override fields to update. Unset fields are not modified.")
class OpeningOverrideUpdateInput:
    date_start: date | None = strawberry.field(default=None, description="New first date (inclusive).")
    date_end: date | None = strawberry.field(default=None, description="New last date (inclusive).")
    weekday: Weekday | None = strawberry.field(
        default=None, description="New weekday the override applies to; null means every day.",
    )
    capacity: int | None = strawberry.field(default=None, description="New overridden capacity.")
    start_time: time | None = strawberry.field(default=None, description="New overridden opening time.")
    end_time: time | None = strawberry.field(default=None, description="New overridden closing time.")
    description: str | None = strawberry.field(default=None, description="New description of this override.")


@strawberry.input(description="New closing information. Bulk: one row is created per weekday in "
                               "`weekdays`; omitted/empty, or all seven, means every day.")
class ServiceClosingCreateInput:
    date_start: date = strawberry.field(description="First date of the closing period (inclusive).")
    date_end: date = strawberry.field(description="Last date of the closing period (inclusive).")
    weekdays: list[Weekday] | None = strawberry.field(
        default=None,
        description="Weekdays to scope to; provide multiple to create one row per weekday.",
    )
    description: str | None = strawberry.field(default=None, description="Description of this closing.")


@strawberry.input(description="Closing fields to update. Unset fields are not modified.")
class ServiceClosingUpdateInput:
    date_start: date | None = strawberry.field(default=None, description="New first date (inclusive).")
    date_end: date | None = strawberry.field(default=None, description="New last date (inclusive).")
    weekday: Weekday | None = strawberry.field(
        default=None, description="New weekday the closing applies to; null means every day.",
    )
    description: str | None = strawberry.field(default=None, description="New description of this closing.")


@strawberry.enum(description="Fields an opening-override search may be sorted by.")
class OpeningOverrideSortField(Enum):
    DATE_START = "date_start"
    DATE_END = "date_end"
    CREATED_AT = "created_at"
    ID = "id"


@strawberry.enum(description="Fields a closing search may be sorted by.")
class ServiceClosingSortField(Enum):
    DATE_START = "date_start"
    DATE_END = "date_end"
    CREATED_AT = "created_at"
    ID = "id"


@strawberry.input(description="Date-range filter for schedule exceptions.")
class ScheduleDateFilter:
    date_from: date | None = strawberry.field(
        default=None, description="Include items whose period ends on or after this date.",
    )
    date_to: date | None = strawberry.field(
        default=None, description="Include items whose period starts on or before this date.",
    )
    include_deleted: bool | None = strawberry.field(
        default=None, description="Return results even if the parent service has been deleted.",
    )


@strawberry.input(description="Opening-override search query.")
class OpeningOverrideSearchInput:
    # `pagination` is optional (not a default_factory) so omitting it stays a plain absent
    # argument — strawberry cannot re-convert a defaulted PaginationInput instance as input.
    pagination: PaginationInput | None = strawberry.field(
        default=None, description="Pagination parameters.",
    )
    sort: list[SortInput[OpeningOverrideSortField]] = strawberry.field(
        default_factory=list, description="Sort instructions.",
    )
    filter: ScheduleDateFilter | None = strawberry.field(
        default=None, description="Filter parameters.",
    )


@strawberry.input(description="Closing search query.")
class ServiceClosingSearchInput:
    pagination: PaginationInput | None = strawberry.field(
        default=None, description="Pagination parameters.",
    )
    sort: list[SortInput[ServiceClosingSortField]] = strawberry.field(
        default_factory=list, description="Sort instructions.",
    )
    filter: ScheduleDateFilter | None = strawberry.field(
        default=None, description="Filter parameters.",
    )


class OpeningOverrideQueryParams(SearchQueryParams):
    """Builds the backend opening-override search query params from an OpeningOverrideSearchInput."""

    def __init__(self, search: OpeningOverrideSearchInput) -> None:
        super().__init__(search.pagination or PaginationInput(), search.sort)
        self._filter = search.filter

    def _finalize(self) -> None:
        if self._filter is None:
            return
        if self._filter.date_from is not None:
            self._set_filter("date_from", self._filter.date_from.isoformat())
        if self._filter.date_to is not None:
            self._set_filter("date_to", self._filter.date_to.isoformat())
        self._set_filter("include_deleted", self._filter.include_deleted)


class ServiceClosingQueryParams(SearchQueryParams):
    """Builds the backend closing search query params from a ServiceClosingSearchInput."""

    def __init__(self, search: ServiceClosingSearchInput) -> None:
        super().__init__(search.pagination or PaginationInput(), search.sort)
        self._filter = search.filter

    def _finalize(self) -> None:
        if self._filter is None:
            return
        if self._filter.date_from is not None:
            self._set_filter("date_from", self._filter.date_from.isoformat())
        if self._filter.date_to is not None:
            self._set_filter("date_to", self._filter.date_to.isoformat())
        self._set_filter("include_deleted", self._filter.include_deleted)


def _override_create_payload(inp: OpeningOverrideCreateInput) -> dict[str, Any]:
    return {
        "date_start": inp.date_start.isoformat(),
        "date_end": inp.date_end.isoformat(),
        "weekdays": [w.value for w in inp.weekdays] if inp.weekdays else None,
        "capacity": inp.capacity,
        "start_time": inp.start_time.isoformat(),
        "end_time": inp.end_time.isoformat(),
        "description": inp.description,
    }


def _override_update_payload(inp: OpeningOverrideUpdateInput) -> dict[str, Any]:
    return {
        "date_start": inp.date_start.isoformat() if inp.date_start is not None else None,
        "date_end": inp.date_end.isoformat() if inp.date_end is not None else None,
        "weekday": inp.weekday.value if inp.weekday is not None else None,
        "capacity": inp.capacity,
        "start_time": inp.start_time.isoformat() if inp.start_time is not None else None,
        "end_time": inp.end_time.isoformat() if inp.end_time is not None else None,
        "description": inp.description,
    }


def _service_closing_create_payload(inp: ServiceClosingCreateInput) -> dict[str, Any]:
    return {
        "date_start": inp.date_start.isoformat(),
        "date_end": inp.date_end.isoformat(),
        "weekdays": [w.value for w in inp.weekdays] if inp.weekdays else None,
        "description": inp.description,
    }


def _service_closing_update_payload(inp: ServiceClosingUpdateInput) -> dict[str, Any]:
    return {
        "date_start": inp.date_start.isoformat() if inp.date_start is not None else None,
        "date_end": inp.date_end.isoformat() if inp.date_end is not None else None,
        "weekday": inp.weekday.value if inp.weekday is not None else None,
        "description": inp.description,
    }


async def resolve_service_opening_overrides(
        service_id: EntityId,
        _input: Annotated[
            OpeningOverrideSearchInput | None,
            strawberry.argument(description="Opening-override search query.", name="input")
        ] = None,
) -> Page[OpeningOverride]:
    search = _input or OpeningOverrideSearchInput()
    params = OpeningOverrideQueryParams(search).build()
    page = await search_service_opening_overrides(service_id, params)
    return Page.from_dict(page, OpeningOverride.from_dict)


async def resolve_create_opening_override(
        service_id: EntityId,
        _input: Annotated[
            OpeningOverrideCreateInput,
            strawberry.argument(description="Opening override information.", name="input")
        ],
) -> list[OpeningOverride]:
    overrides = await create_service_opening_overrides(service_id, _override_create_payload(_input))
    return [OpeningOverride.from_dict(override) for override in overrides]


async def resolve_update_opening_override(
        service_id: EntityId,
        override_id: Annotated[strawberry.ID, strawberry.argument(description="Opening override ID.")],
        _input: Annotated[
            OpeningOverrideUpdateInput,
            strawberry.argument(description="Opening override fields to update.", name="input")
        ],
) -> OpeningOverride:
    override = await update_service_opening_override(service_id, override_id, _override_update_payload(_input))
    return OpeningOverride.from_dict(override)


async def resolve_delete_opening_override(
        service_id: EntityId,
        override_id: Annotated[strawberry.ID, strawberry.argument(description="Opening override ID.")],
) -> bool:
    """Delete an opening override. Returns True when the deletion succeeds."""
    await delete_service_opening_override(service_id, override_id)
    return True


async def resolve_service_closings(
        service_id: EntityId,
        _input: Annotated[
            ServiceClosingSearchInput | None,
            strawberry.argument(description="Closing search query.", name="input")
        ] = None,
) -> Page[ServiceClosing]:
    search = _input or ServiceClosingSearchInput()
    params = ServiceClosingQueryParams(search).build()
    page = await search_service_closings(service_id, params)
    return Page.from_dict(page, ServiceClosing.from_dict)


async def resolve_create_service_closing(
        service_id: EntityId,
        _input: Annotated[
            ServiceClosingCreateInput,
            strawberry.argument(description="Closing information.", name="input")
        ],
) -> list[ServiceClosing]:
    closings = await create_service_closings(service_id, _service_closing_create_payload(_input))
    return [ServiceClosing.from_dict(closing) for closing in closings]


async def resolve_update_service_closing(
        service_id: EntityId,
        closing_id: Annotated[strawberry.ID, strawberry.argument(description="Closing ID.")],
        _input: Annotated[
            ServiceClosingUpdateInput,
            strawberry.argument(description="Closing fields to update.", name="input")
        ],
) -> ServiceClosing:
    closing = await update_service_closing(service_id, closing_id, _service_closing_update_payload(_input))
    return ServiceClosing.from_dict(closing)


async def resolve_delete_service_closing(
        service_id: EntityId,
        closing_id: Annotated[strawberry.ID, strawberry.argument(description="Closing ID.")],
) -> bool:
    """Delete a closing. Returns True when the deletion succeeds."""
    await delete_service_closing(service_id, closing_id)
    return True


@strawberry.type(description="A seat-count delta applied on top of the resolved capacity for a date range.")
class CapacityOverride:
    id: str = strawberry.field(description="Capacity override identifier.")
    service_id: str = strawberry.field(description="Identifier of the service this override belongs to.")
    date_start: date = strawberry.field(description="First date of the override period (inclusive).")
    date_end: date = strawberry.field(description="Last date of the override period (inclusive).")
    weekday: Weekday | None = strawberry.field(
        description="Weekday the override applies to within the range; null means every day.",
    )
    capacity_delta: int = strawberry.field(description="Signed change to the resolved seat count.")
    description: str | None = strawberry.field(description="Description of this capacity override.")
    created_at: datetime = strawberry.field(description="Creation date.")
    updated_at: datetime = strawberry.field(description="Last update date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "CapacityOverride":
        return CapacityOverride(
            id=obj["id"],
            service_id=obj["service_id"],
            date_start=obj["date_start"],
            date_end=obj["date_end"],
            weekday=Weekday(obj["weekday"]) if obj.get("weekday") else None,
            capacity_delta=obj["capacity_delta"],
            description=obj.get("description"),
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


@strawberry.input(description="New capacity override information. Bulk: one row is created per "
                               "weekday in `weekdays`; omitted/empty, or all seven, means every day.")
class CapacityOverrideCreateInput:
    date_start: date = strawberry.field(description="First date of the override period (inclusive).")
    date_end: date = strawberry.field(description="Last date of the override period (inclusive).")
    weekdays: list[Weekday] | None = strawberry.field(
        default=None,
        description="Weekdays to scope to; provide multiple to create one row per weekday.",
    )
    capacity_delta: int = strawberry.field(description="Signed change to the resolved seat count.")
    description: str | None = strawberry.field(default=None, description="Description of this capacity override.")


@strawberry.input(description="Capacity override fields to update. Unset fields are not modified.")
class CapacityOverrideUpdateInput:
    date_start: date | None = strawberry.field(default=None, description="New first date (inclusive).")
    date_end: date | None = strawberry.field(default=None, description="New last date (inclusive).")
    weekday: Weekday | None = strawberry.field(
        default=None, description="New weekday the override applies to; null means every day.",
    )
    capacity_delta: int | None = strawberry.field(default=None, description="New signed seat-count change.")
    description: str | None = strawberry.field(default=None, description="New description of this override.")


@strawberry.enum(description="Fields a capacity-override search may be sorted by.")
class CapacityOverrideSortField(Enum):
    DATE_START = "date_start"
    DATE_END = "date_end"
    CREATED_AT = "created_at"
    ID = "id"


@strawberry.input(description="Capacity-override search query.")
class CapacityOverrideSearchInput:
    pagination: PaginationInput | None = strawberry.field(
        default=None, description="Pagination parameters.",
    )
    sort: list[SortInput[CapacityOverrideSortField]] = strawberry.field(
        default_factory=list, description="Sort instructions.",
    )
    filter: ScheduleDateFilter | None = strawberry.field(
        default=None, description="Filter parameters.",
    )


class CapacityOverrideQueryParams(SearchQueryParams):
    """Builds the backend capacity-override search query params from a CapacityOverrideSearchInput."""

    def __init__(self, search: CapacityOverrideSearchInput) -> None:
        super().__init__(search.pagination or PaginationInput(), search.sort)
        self._filter = search.filter

    def _finalize(self) -> None:
        if self._filter is None:
            return
        if self._filter.date_from is not None:
            self._set_filter("date_from", self._filter.date_from.isoformat())
        if self._filter.date_to is not None:
            self._set_filter("date_to", self._filter.date_to.isoformat())
        self._set_filter("include_deleted", self._filter.include_deleted)


def _capacity_override_create_payload(inp: CapacityOverrideCreateInput) -> dict[str, Any]:
    return {
        "date_start": inp.date_start.isoformat(),
        "date_end": inp.date_end.isoformat(),
        "weekdays": [w.value for w in inp.weekdays] if inp.weekdays else None,
        "capacity_delta": inp.capacity_delta,
        "description": inp.description,
    }


def _capacity_override_update_payload(inp: CapacityOverrideUpdateInput) -> dict[str, Any]:
    return {
        "date_start": inp.date_start.isoformat() if inp.date_start is not None else None,
        "date_end": inp.date_end.isoformat() if inp.date_end is not None else None,
        "weekday": inp.weekday.value if inp.weekday is not None else None,
        "capacity_delta": inp.capacity_delta,
        "description": inp.description,
    }


async def resolve_service_capacity_overrides(
        service_id: EntityId,
        _input: Annotated[
            CapacityOverrideSearchInput | None,
            strawberry.argument(description="Capacity-override search query.", name="input")
        ] = None,
) -> Page[CapacityOverride]:
    search = _input or CapacityOverrideSearchInput()
    params = CapacityOverrideQueryParams(search).build()
    page = await search_service_capacity_overrides(service_id, params)
    return Page.from_dict(page, CapacityOverride.from_dict)


async def resolve_create_capacity_override(
        service_id: EntityId,
        _input: Annotated[
            CapacityOverrideCreateInput,
            strawberry.argument(description="Capacity override information.", name="input")
        ],
) -> list[CapacityOverride]:
    capacity_overrides = await create_service_capacity_overrides(
        service_id, _capacity_override_create_payload(_input)
    )
    return [
        CapacityOverride.from_dict(capacity_override)
        for capacity_override in capacity_overrides
    ]


async def resolve_update_capacity_override(
        service_id: EntityId,
        capacity_override_id: Annotated[strawberry.ID, strawberry.argument(description="Capacity override ID.")],
        _input: Annotated[
            CapacityOverrideUpdateInput,
            strawberry.argument(description="Capacity override fields to update.", name="input")
        ],
) -> CapacityOverride:
    capacity_override = await update_service_capacity_override(
        service_id, capacity_override_id, _capacity_override_update_payload(_input)
    )
    return CapacityOverride.from_dict(capacity_override)


async def resolve_delete_capacity_override(
        service_id: EntityId,
        capacity_override_id: Annotated[strawberry.ID, strawberry.argument(description="Capacity override ID.")],
) -> bool:
    """Delete a capacity override. Returns True when the deletion succeeds."""
    await delete_service_capacity_override(service_id, capacity_override_id)
    return True


@strawberry.type(description="A venue-wide closing: closes every service of a venue for a date range.")
class VenueClosing:
    id: str = strawberry.field(description="Venue closing identifier.")
    venue_id: str = strawberry.field(description="Identifier of the venue this closing belongs to.")
    date_start: date = strawberry.field(description="First date of the closing period (inclusive).")
    date_end: date = strawberry.field(description="Last date of the closing period (inclusive).")
    weekday: Weekday | None = strawberry.field(
        description="Weekday the closing applies to within the range; null means every day.",
    )
    description: str | None = strawberry.field(description="Description of this venue closing.")
    created_at: datetime = strawberry.field(description="Creation date.")
    updated_at: datetime = strawberry.field(description="Last update date.")

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> "VenueClosing":
        return VenueClosing(
            id=obj["id"],
            venue_id=obj["venue_id"],
            date_start=obj["date_start"],
            date_end=obj["date_end"],
            weekday=Weekday(obj["weekday"]) if obj.get("weekday") else None,
            description=obj.get("description"),
            created_at=obj["created_at"],
            updated_at=obj["updated_at"],
        )


@strawberry.input(description="New venue closing information. Bulk: one row is created per "
                               "weekday in `weekdays`; omitted/empty, or all seven, means every day.")
class VenueClosingCreateInput:
    date_start: date = strawberry.field(description="First date of the closing period (inclusive).")
    date_end: date = strawberry.field(description="Last date of the closing period (inclusive).")
    weekdays: list[Weekday] | None = strawberry.field(
        default=None,
        description="Weekdays to scope to; provide multiple to create one row per weekday.",
    )
    description: str | None = strawberry.field(default=None, description="Description of this venue closing.")


@strawberry.input(description="Venue closing fields to update. Unset fields are not modified.")
class VenueClosingUpdateInput:
    date_start: date | None = strawberry.field(default=None, description="New first date (inclusive).")
    date_end: date | None = strawberry.field(default=None, description="New last date (inclusive).")
    weekday: Weekday | None = strawberry.field(
        default=None, description="New weekday the closing applies to; null means every day.",
    )
    description: str | None = strawberry.field(default=None, description="New description of this closing.")


@strawberry.enum(description="Fields a venue-closing search may be sorted by.")
class VenueClosingSortField(Enum):
    DATE_START = "date_start"
    DATE_END = "date_end"
    CREATED_AT = "created_at"
    ID = "id"


@strawberry.input(description="Venue-closing search query.")
class VenueClosingSearchInput:
    pagination: PaginationInput | None = strawberry.field(
        default=None, description="Pagination parameters.",
    )
    sort: list[SortInput[VenueClosingSortField]] = strawberry.field(
        default_factory=list, description="Sort instructions.",
    )
    filter: ScheduleDateFilter | None = strawberry.field(
        default=None, description="Filter parameters.",
    )


class VenueClosingQueryParams(SearchQueryParams):
    """Builds the backend venue-closing search query params from a VenueClosingSearchInput."""

    def __init__(self, search: VenueClosingSearchInput) -> None:
        super().__init__(search.pagination or PaginationInput(), search.sort)
        self._filter = search.filter

    def _finalize(self) -> None:
        if self._filter is None:
            return
        if self._filter.date_from is not None:
            self._set_filter("date_from", self._filter.date_from.isoformat())
        if self._filter.date_to is not None:
            self._set_filter("date_to", self._filter.date_to.isoformat())


def _venue_closing_create_payload(inp: VenueClosingCreateInput) -> dict[str, Any]:
    return {
        "date_start": inp.date_start.isoformat(),
        "date_end": inp.date_end.isoformat(),
        "weekdays": [w.value for w in inp.weekdays] if inp.weekdays else None,
        "description": inp.description,
    }


def _venue_closing_update_payload(inp: VenueClosingUpdateInput) -> dict[str, Any]:
    return {
        "date_start": inp.date_start.isoformat() if inp.date_start is not None else None,
        "date_end": inp.date_end.isoformat() if inp.date_end is not None else None,
        "weekday": inp.weekday.value if inp.weekday is not None else None,
        "description": inp.description,
    }


async def resolve_venue_closings(
        venue_id: EntityId,
        _input: Annotated[
            VenueClosingSearchInput | None,
            strawberry.argument(description="Venue-closing search query.", name="input")
        ] = None,
) -> Page[VenueClosing]:
    search = _input or VenueClosingSearchInput()
    params = VenueClosingQueryParams(search).build()
    page = await search_venue_closings(venue_id, params)
    return Page.from_dict(page, VenueClosing.from_dict)


async def resolve_create_venue_closing(
        venue_id: EntityId,
        _input: Annotated[
            VenueClosingCreateInput,
            strawberry.argument(description="Venue closing information.", name="input")
        ],
) -> list[VenueClosing]:
    closings = await create_venue_closings(venue_id, _venue_closing_create_payload(_input))
    return [VenueClosing.from_dict(closing) for closing in closings]


async def resolve_update_venue_closing(
        venue_id: EntityId,
        closing_id: Annotated[strawberry.ID, strawberry.argument(description="Venue closing ID.")],
        _input: Annotated[
            VenueClosingUpdateInput,
            strawberry.argument(description="Venue closing fields to update.", name="input")
        ],
) -> VenueClosing:
    closing = await update_venue_closing(venue_id, closing_id, _venue_closing_update_payload(_input))
    return VenueClosing.from_dict(closing)


async def resolve_delete_venue_closing(
        venue_id: EntityId,
        closing_id: Annotated[strawberry.ID, strawberry.argument(description="Venue closing ID.")],
) -> bool:
    """Delete a venue closing. Returns True when the deletion succeeds."""
    await delete_venue_closing(venue_id, closing_id)
    return True


@strawberry.type
class ScheduleQuery:
    service_openings: list[Opening] = strawberry.field(
        resolver=resolve_service_openings,
        description="List the weekly openings for a service.",
    )
    venue_closings: Page[VenueClosing] = strawberry.field(
        resolver=resolve_venue_closings,
        description="Search the venue-wide closings for a venue.",
    )
    service_opening_overrides: Page[OpeningOverride] = strawberry.field(
        resolver=resolve_service_opening_overrides,
        description="Search the opening overrides for a service.",
    )
    service_closings: Page[ServiceClosing] = strawberry.field(
        resolver=resolve_service_closings,
        description="Search the closings for a service.",
    )
    service_capacity_overrides: Page[CapacityOverride] = strawberry.field(
        resolver=resolve_service_capacity_overrides,
        description="Search the capacity overrides for a service.",
    )


@strawberry.type
class ScheduleMutation:
    upsert_service_openings = strawberry.mutation(
        resolver=resolve_upsert_service_openings,
        description="Replace the full set of weekly openings for a service.",
    )
    create_opening_override = strawberry.mutation(
        resolver=resolve_create_opening_override,
        description="Create a new opening override for a service.",
    )
    update_opening_override = strawberry.mutation(
        resolver=resolve_update_opening_override,
        description="Update an opening override.",
    )
    delete_opening_override = strawberry.mutation(
        resolver=resolve_delete_opening_override,
        description="Delete an opening override.",
    )
    create_service_closing = strawberry.mutation(
        resolver=resolve_create_service_closing,
        description="Create a new closing for a service.",
    )
    update_service_closing = strawberry.mutation(
        resolver=resolve_update_service_closing,
        description="Update a closing.",
    )
    delete_service_closing = strawberry.mutation(
        resolver=resolve_delete_service_closing,
        description="Delete a closing.",
    )
    create_capacity_override = strawberry.mutation(
        resolver=resolve_create_capacity_override,
        description="Create a new capacity override for a service.",
    )
    update_capacity_override = strawberry.mutation(
        resolver=resolve_update_capacity_override,
        description="Update a capacity override.",
    )
    delete_capacity_override = strawberry.mutation(
        resolver=resolve_delete_capacity_override,
        description="Delete a capacity override.",
    )
    create_venue_closing = strawberry.mutation(
        resolver=resolve_create_venue_closing,
        description="Create a new venue-wide closing.",
    )
    update_venue_closing = strawberry.mutation(
        resolver=resolve_update_venue_closing,
        description="Update a venue-wide closing.",
    )
    delete_venue_closing = strawberry.mutation(
        resolver=resolve_delete_venue_closing,
        description="Delete a venue-wide closing.",
    )

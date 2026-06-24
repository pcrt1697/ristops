from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Callable, Generic, TypeVar

import strawberry

T = TypeVar("T")
F = TypeVar("F", bound=Enum)


@strawberry.enum(description="Direction of a sort clause.")
class SortDirection(Enum):
    ASC = "asc"
    DESC = "desc"


@strawberry.input(description="Pagination parameters.")
class PaginationInput:
    page: int = strawberry.field(default=0, description="0-indexed page number.")
    page_size: int = strawberry.field(default=20, description="Items per page.")


@strawberry.input(description="A single sort instruction.")
class SortInput(Generic[F]):
    field: F = strawberry.field(description="Field to sort by.")
    direction: SortDirection = strawberry.field(
        default=SortDirection.ASC,
        description="Sort direction.",
    )


@strawberry.type(description="A single page of results with pagination metadata.")
class Page(Generic[T]):
    items: list[T] = strawberry.field(description="Items in the current page.")
    total: int = strawberry.field(description="Total number of items across all pages.")
    page: int = strawberry.field(description="0-indexed page number.")
    page_size: int = strawberry.field(description="Number of items per page.")
    total_pages: int = strawberry.field(description="Total number of pages.")

    @classmethod
    def from_dict(
            cls,
            obj: dict[str, Any],
            item_factory: Callable[[dict[str, Any]], T],
    ) -> "Page[T]":
        """Build a page from a backend response dict, mapping each item with `item_factory`."""
        return cls(
            items=[item_factory(item) for item in obj["items"]],
            total=obj["total"],
            page=obj["page"],
            page_size=obj["page_size"],
            total_pages=obj["total_pages"],
        )


class SearchQueryParams(ABC):
    """Builds the backend search query params from pagination and sort.

    Subclasses implement `_finalize` to add their `filter.<name>` params, typically
    via `self._set_filter(...)`.
    """

    def __init__(self, pagination: PaginationInput, sort: list[SortInput]) -> None:
        self._params: dict[str, Any] = {
            "page": pagination.page,
            "page_size": pagination.page_size,
        }
        if sort:
            self._params["sort"] = [self._encode_sort(clause) for clause in sort]

    @staticmethod
    def _encode_sort(clause: SortInput) -> str:
        """Encode a sort clause as the backend expects, prefixing '-' for descending."""
        field = clause.field.value
        return f"-{field}" if clause.direction is SortDirection.DESC else field

    def _set_filter(self, name: str, value: Any) -> None:
        """Add a `filter.<name>` param when `value` is set."""
        if value is not None:
            self._params[f"filter.{name}"] = value

    @abstractmethod
    def _finalize(self) -> None:
        """Add the subclass's filter params (e.g. via `self._set_filter(...)`)."""

    def build(self) -> dict[str, Any]:
        """Return the query params dict to pass to the backend search request."""
        self._finalize()
        return self._params

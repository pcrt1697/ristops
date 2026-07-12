from enum import Enum, StrEnum
from math import ceil
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator


class SortDirection(str, Enum):
    """Direction of a sort clause."""

    ASC = "asc"
    DESC = "desc"


class PaginationParams(BaseModel):
    """Pagination query parameters."""

    page: int = Field(default=0, ge=0, description="0-indexed page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")


class SortClause(BaseModel):
    """A single parsed sort instruction: a field name and a direction."""

    field: str = Field(description="Field name")
    direction: SortDirection = SortDirection.ASC


_NON_FILTER_FIELDS = frozenset({"page", "page_size", "sort"})


def query_alias(field_name: str) -> str:
    """Prefix filter fields with 'filter.'; leave pagination and sort fields bare."""
    return field_name if field_name in _NON_FILTER_FIELDS else f"filter.{field_name}"


class SortableQuery(BaseModel):
    """Base search query: sort, plus filter fields mixed in by a subclass.

    Compose with a filter model and set ``sort_field_enum`` to a ``StrEnum`` of the
    sortable fields::

        class VenueSearchFilter(BaseModel):
            name: str | None = None

        class VenueSearchQuery(SortableQuery, VenueSearchFilter):
            sort_field_enum: ClassVar[type[StrEnum]] = VenueSortField

    Filter fields are exposed as ``filter.<name>`` query params; sort stays bare. The
    enum both validates submitted sort fields and feeds the OpenAPI description.
    Clients pass a repeatable ``sort`` param, prefixing a field with ``-`` for
    descending: ``?sort=name&sort=-created_at``.

    Combine with ``PaginationParams`` (see ``SearchQuery``) when the result set needs
    paging; use this alone for small, unpaginated result sets.
    """

    model_config = ConfigDict(alias_generator=query_alias, populate_by_name=True)

    sort: list[str] = Field(
        default_factory=list,
        description="Repeatable. Prefix a field with '-' for descending.",
    )

    sort_field_enum: ClassVar[type[StrEnum]]

    _sort_clauses: list[SortClause] = PrivateAttr(default_factory=list)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Embed `sort_field_enum`'s fields into the `sort` description, once a concrete
        subclass sets it. Intermediate/abstract bases (e.g. `SearchQuery`) that don't yet
        declare `sort_field_enum` are left as-is; a genuinely misconfigured leaf class will
        fail when a query is actually parsed, in `_parse_and_validate_sort` below."""
        super().__pydantic_init_subclass__(**kwargs)
        sort_field_enum = getattr(cls, "sort_field_enum", None)
        if sort_field_enum is None:
            return
        fields = ", ".join(member.value for member in sort_field_enum)
        cls.model_fields["sort"].description = (
            f"Sortable fields: {fields}. Prefix a field with '-' for descending."
        )
        cls.model_rebuild(force=True)

    @model_validator(mode="after")
    def _parse_and_validate_sort(self) -> "SortableQuery":
        """Parse the raw sort strings into validated clauses against the enum."""
        allowed = {member.value for member in type(self).sort_field_enum}
        clauses: list[SortClause] = []
        for raw in self.sort:
            raw = raw.strip()
            if not raw:
                continue
            descending = raw.startswith("-")
            field_name = raw[1:] if descending else raw
            if field_name not in allowed:
                valid = ", ".join(sorted(allowed))
                raise ValueError(
                    f"Invalid sort field '{field_name}'. Valid fields: {valid}"
                )
            clauses.append(
                SortClause(
                    field=field_name,
                    direction=SortDirection.DESC if descending else SortDirection.ASC,
                )
            )
        self._sort_clauses = clauses
        return self

    def get_sort_clauses(self) -> list[SortClause]:
        """Parsed, validated sort clauses in the order given by the client."""
        return self._sort_clauses or [
            SortClause(
                field=next(iter(self.sort_field_enum)).value,
            )
        ]


class SearchQuery(SortableQuery, PaginationParams):
    """Base search query: pagination + sort, plus filter fields mixed in by a subclass.

    See ``SortableQuery`` for the sort/filter mechanism this adds pagination to.
    """


class Page[TItem](BaseModel):
    """A single page of results plus pagination metadata."""

    items: list[TItem]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(cls, items: list[TItem], total: int, params: PaginationParams) -> "Page[TItem]":
        """Build a Page from its items, the total count, and the pagination params used."""
        total_pages = ceil(total / params.page_size) if params.page_size else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

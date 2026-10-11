from enum import StrEnum
from typing import Annotated, ClassVar

import pytest
from fastapi import FastAPI, Query
from pydantic import BaseModel, ValidationError

from helpers import make_client
from ristops_lib_core.schema.pagination import (
    Page, PaginationParams, SearchQuery, SortClause, SortDirection, SortableQuery, query_alias,
)


class VenueSortField(StrEnum):
    NAME = "name"
    CREATED_AT = "created_at"


class VenueFilter(BaseModel):
    name: str | None = None
    city: str | None = None


class VenueSortQuery(SortableQuery, VenueFilter):
    sort_field_enum: ClassVar[type[StrEnum]] = VenueSortField


class VenueSearchQuery(SearchQuery, VenueFilter):
    sort_field_enum: ClassVar[type[StrEnum]] = VenueSortField


class TestPaginationParams:

    def test_defaults(self):
        params = PaginationParams()

        assert (params.page, params.page_size) == (0, 20)

    @pytest.mark.parametrize("values", [{"page": -1}, {"page_size": 0}, {"page_size": 101}])
    def test_out_of_range_values_are_rejected(self, values: dict):
        with pytest.raises(ValidationError):
            PaginationParams(**values)

    @pytest.mark.parametrize("values", [{"page": 0}, {"page_size": 1}, {"page_size": 100}, {"page": 999}])
    def test_limits_are_inclusive(self, values: dict):
        assert PaginationParams(**values)


class TestSortClause:

    def test_direction_defaults_to_ascending(self):
        assert SortClause(field="name").direction is SortDirection.ASC

    def test_direction_values(self):
        assert {SortDirection.ASC, SortDirection.DESC} == {"asc", "desc"}


class TestQueryAlias:

    @pytest.mark.parametrize("field", ["page", "page_size", "sort"])
    def test_pagination_and_sort_stay_bare(self, field: str):
        assert query_alias(field) == field

    @pytest.mark.parametrize("field", ["name", "venue_id", "created_at"])
    def test_every_other_field_is_a_filter(self, field: str):
        assert query_alias(field) == f"filter.{field}"


class TestSortableQuery:

    def test_parses_ascending_and_descending_clauses_in_order(self):
        query = VenueSortQuery(sort=["name", "-created_at"])

        assert query.get_sort_clauses() == [
            SortClause(field="name", direction=SortDirection.ASC),
            SortClause(field="created_at", direction=SortDirection.DESC),
        ]

    def test_defaults_to_the_first_field_of_the_enum_when_nothing_is_requested(self):
        assert VenueSortQuery().get_sort_clauses() == [SortClause(field="name", direction=SortDirection.ASC)]

    def test_blank_entries_are_ignored(self):
        query = VenueSortQuery(sort=["", "  ", " -name "])

        assert query.get_sort_clauses() == [SortClause(field="name", direction=SortDirection.DESC)]

    def test_only_blank_entries_fall_back_to_the_default(self):
        assert VenueSortQuery(sort=[" "]).get_sort_clauses()[0].field == "name"

    @pytest.mark.parametrize("value", ["unknown", "-unknown", "Name", "--name"])
    def test_a_field_outside_the_enum_is_rejected_and_the_valid_ones_are_listed(self, value: str):
        with pytest.raises(ValidationError, match="Valid fields: created_at, name"):
            VenueSortQuery(sort=[value])

    def test_filters_are_read_by_their_prefixed_alias(self):
        query = VenueSortQuery.model_validate({"filter.name": "Roma", "filter.city": "Rome"})

        assert (query.name, query.city) == ("Roma", "Rome")

    def test_filters_can_also_be_set_by_field_name(self):
        assert VenueSortQuery(name="Roma").name == "Roma"

    def test_the_sort_field_keeps_its_bare_name(self):
        assert VenueSortQuery.model_validate({"sort": ["-name"]}).sort == ["-name"]

    def test_dumping_by_alias_prefixes_the_filters(self):
        dumped = VenueSortQuery(name="Roma").model_dump(by_alias=True, exclude_none=True, exclude={"sort"})

        assert dumped == {"filter.name": "Roma"}

    def test_the_sort_description_lists_the_sortable_fields(self):
        description = VenueSortQuery.model_fields["sort"].description

        assert "name, created_at" in description
        assert "'-'" in description

    def test_each_query_class_describes_only_its_own_fields(self):
        class OtherField(StrEnum):
            PRICE = "price"

        class OtherQuery(SortableQuery):
            sort_field_enum: ClassVar[type[StrEnum]] = OtherField

        assert "price" in OtherQuery.model_fields["sort"].description
        assert "price" not in VenueSortQuery.model_fields["sort"].description

    def test_a_query_without_a_sort_enum_fails_when_it_is_parsed(self):
        class Misconfigured(SortableQuery):
            pass

        with pytest.raises(AttributeError):
            Misconfigured()


class TestSearchQuery:

    def test_combines_pagination_sort_and_filters(self):
        query = VenueSearchQuery.model_validate({"page": 2, "page_size": 5, "sort": ["-name"], "filter.city": "Rome"})

        assert (query.page, query.page_size, query.city) == (2, 5, "Rome")
        assert query.get_sort_clauses()[0].direction is SortDirection.DESC

    def test_pagination_defaults_apply(self):
        query = VenueSearchQuery()

        assert (query.page, query.page_size) == (0, 20)

    def test_pagination_limits_apply(self):
        with pytest.raises(ValidationError):
            VenueSearchQuery(page_size=500)

    def test_pagination_names_are_not_prefixed(self):
        aliases = {field.alias for field in VenueSearchQuery.model_fields.values()}

        assert {"page", "page_size", "sort", "filter.name", "filter.city"} <= aliases


class TestAsQueryParameters:

    @staticmethod
    def build_app() -> FastAPI:
        app = FastAPI()

        @app.get("/venues")
        async def search(query: Annotated[VenueSearchQuery, Query()]) -> dict:
            return {
                "name": query.name,
                "page": query.page,
                "sort": [f"{c.field}:{c.direction.value}" for c in query.get_sort_clauses()],
            }

        return app

    @pytest.mark.anyio
    async def test_the_prefixed_query_parameters_reach_the_model(self):
        async with make_client(self.build_app()) as client:
            response = await client.get(
                "/venues", params={"filter.name": "Roma", "page": 3, "sort": ["name", "-created_at"]},
            )

        assert response.json() == {"name": "Roma", "page": 3, "sort": ["name:asc", "created_at:desc"]}

    @pytest.mark.anyio
    async def test_an_invalid_sort_is_a_422(self):
        async with make_client(self.build_app()) as client:
            response = await client.get("/venues", params={"sort": "bogus"})

        assert response.status_code == 422

    @pytest.mark.anyio
    async def test_the_openapi_schema_lists_the_prefixed_parameters(self):
        async with make_client(self.build_app()) as client:
            schema = (await client.get("/openapi.json")).json()

        names = {parameter["name"] for parameter in schema["paths"]["/venues"]["get"]["parameters"]}
        assert {"filter.name", "filter.city", "page", "page_size", "sort"} == names


class TestPage:

    @pytest.mark.parametrize("total, page_size, expected", [
        (0, 20, 0), (1, 20, 1), (20, 20, 1), (21, 20, 2), (45, 20, 3), (40, 20, 2), (7, 1, 7), (100, 100, 1),
    ])
    def test_total_pages_rounds_up(self, total: int, page_size: int, expected: int):
        page = Page[str].create(["x"], total, PaginationParams(page_size=page_size))

        assert page.total_pages == expected

    def test_carries_the_items_and_the_pagination_used(self):
        page = Page[str].create(["a", "b"], 12, PaginationParams(page=1, page_size=2))

        assert page.model_dump() == {"items": ["a", "b"], "total": 12, "page": 1, "page_size": 2, "total_pages": 6}

    def test_items_are_validated_against_the_item_type(self):
        with pytest.raises(ValidationError):
            Page[int].create(["not-a-number"], 1, PaginationParams())

    def test_an_empty_page(self):
        page = Page[str].create([], 0, PaginationParams())

        assert (page.items, page.total, page.total_pages) == ([], 0, 0)

    def test_the_item_type_shows_up_in_the_schema_name(self):
        assert Page[VenueFilter].__name__ == "Page[VenueFilter]"

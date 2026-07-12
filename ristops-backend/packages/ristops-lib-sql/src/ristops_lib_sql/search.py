from typing import Callable, Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import ScalarResult, select, ColumnElement, UnaryExpression, func, Select
from sqlalchemy.orm import DeclarativeBase, Mapped

from ristops_lib_core.schema.pagination import Page, SearchQuery, SortableQuery, SortClause, SortDirection
from ristops_lib_sql.engine import get_sql_session

TQuery = TypeVar("TQuery", bound=SortableQuery)
TPagedQuery = TypeVar("TPagedQuery", bound=SearchQuery)
TScope = TypeVar("TScope")
TEntity = TypeVar("TEntity", bound=DeclarativeBase)
TResponse = TypeVar("TResponse", bound=BaseModel)


class BaseModelMapper(Generic[TEntity, TResponse]):
    """Default model mapper that uses Pydantic's model_validate to convert an ORM entity to a response model."""

    def __init__(self, response_class: type[TResponse]) -> None:
        self._response_class = response_class

    def __call__(self, entity: TEntity) -> TResponse:
        return self._response_class.model_validate(entity, from_attributes=True, extra="ignore")


class BaseSortParser(Generic[TEntity]):
    """Default sort parser that maps SortClause fields to SQLAlchemy order expressions on the given entity class."""

    def __init__(self, entity_class: type[TEntity]) -> None:
        self._entity_class = entity_class

    def __call__(self, sort_clauses: list[SortClause]) -> list[UnaryExpression]:
        expressions = []
        for clause in sort_clauses:
            if not hasattr(self._entity_class, clause.field):
                raise ValueError(
                    f"Entity '{self._entity_class.__name__}' has no field '{clause.field}'."
                )
            field: Mapped[Any] = getattr(self._entity_class, clause.field)
            expression = field.desc() if clause.direction == SortDirection.DESC else field.asc()
            expressions.append(expression)
        return expressions


class SearchQueryExecutor(Generic[TQuery, TScope, TEntity, TResponse]):
    """Executes a filtered and sorted search query against a SQLAlchemy model. Not paginated.

    See `PaginatedSearchQueryExecutor` for the paginated counterpart, which composes this class.
    """

    def __init__(
            self,
            entity_class: type[TEntity],
            response_class: type[TResponse],
            condition_builder: Callable[[TQuery, TScope], list[ColumnElement[bool]]],
            sort_parser: Callable[[list[SortClause]], list[UnaryExpression]] | None = None,
            model_mapper: Callable[[TEntity], TResponse] | None = None,
    ) -> None:
        self.entity_class = entity_class
        self._build_condition = condition_builder
        self._parse_sort = sort_parser if sort_parser is not None else BaseSortParser(entity_class)
        self._map_item: Callable[[TEntity], TResponse] = model_mapper if model_mapper is not None else BaseModelMapper(
            response_class)

    def build_conditions(self, query: TQuery, scope: TScope) -> list[ColumnElement[bool]]:
        """Build the WHERE conditions for the query, from the user filter and the given scope."""
        return self._build_condition(query, scope)

    def build_statement(
            self,
            query: TQuery,
            scope: TScope,
            conditions: list[ColumnElement[bool]] | None = None,
    ) -> Select:
        """Build the base SELECT statement (WHERE + ORDER BY), without offset/limit."""
        conditions = conditions if conditions is not None else self.build_conditions(query, scope)
        stmt = select(self.entity_class).where(*conditions)
        sort_clauses = query.get_sort_clauses()
        if sort_clauses:
            stmt = stmt.order_by(*self._parse_sort(sort_clauses))
        return stmt

    def map_items(self, entities: list[TEntity]) -> list[TResponse]:
        """Map a list of ORM entities to their response models."""
        return [self._map_item(entity) for entity in entities]

    async def execute(self, query: TQuery, scope: TScope) -> list[TResponse]:
        """
        Execute the search and return the matching response models. Not paginated.

        :param query: Search query defined by the user.
        :param scope: Scope that defines additional filters forced by the application (e.g. authorization filters).
        """
        session = get_sql_session()
        stmt = self.build_statement(query, scope)
        result: ScalarResult[TEntity] = await session.scalars(stmt)
        return self.map_items(result.all())


class PaginatedSearchQueryExecutor(Generic[TPagedQuery, TScope, TEntity, TResponse]):
    """Executes a paginated, filtered, and sorted search query against a SQLAlchemy model.

    Composes a `SearchQueryExecutor` for condition-building, sorting, and mapping, and adds
    offset/limit and a total count on top.
    """

    def __init__(
            self,
            entity_class: type[TEntity],
            response_class: type[TResponse],
            condition_builder: Callable[[TPagedQuery, TScope], list[ColumnElement[bool]]],
            sort_parser: Callable[[list[SortClause]], list[UnaryExpression]] | None = None,
            model_mapper: Callable[[TEntity], TResponse] | None = None,
    ) -> None:
        self._executor: SearchQueryExecutor[TPagedQuery, TScope, TEntity, TResponse] = SearchQueryExecutor(
            entity_class, response_class, condition_builder, sort_parser, model_mapper,
        )

    async def execute(self, query: TPagedQuery, scope: TScope) -> Page[TResponse]:
        """
        Execute the search and return a paginated page of response models.

        :param query: Search query defined by the user.
        :param scope: Scope that defines additional filters forced by the application (e.g. authorization filters).
        """
        session = get_sql_session()
        conditions = self._executor.build_conditions(query, scope)
        stmt = self._executor.build_statement(query, scope, conditions)

        offset = query.page * query.page_size
        stmt = stmt.offset(offset).limit(query.page_size)

        total_items = await session.scalar(
            select(func.count()).select_from(self._executor.entity_class).where(*conditions)
        )
        result: ScalarResult[TEntity] = await session.scalars(stmt)
        items = self._executor.map_items(result.all())
        return Page.create(
            items=items,
            total=total_items or 0,
            params=query,
        )

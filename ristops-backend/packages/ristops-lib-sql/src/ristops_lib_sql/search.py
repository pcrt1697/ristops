from typing import Callable, Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import ScalarResult, select, ColumnElement, UnaryExpression, func
from sqlalchemy.orm import DeclarativeBase, Mapped

from ristops_lib_core.schema.pagination import Page, SearchQuery, SortClause, SortDirection
from ristops_lib_sql.engine import get_sql_session

TQuery = TypeVar("TQuery", bound=SearchQuery)
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
    """Executes a paginated, filtered, and sorted search query against a SQLAlchemy model."""

    def __init__(
            self,
            entity_class: type[TEntity],
            response_class: type[TResponse],
            condition_builder: Callable[[TQuery, TScope], list[ColumnElement[bool]]],
            sort_parser: Callable[[list[SortClause]], list[UnaryExpression]] | None = None,
            model_mapper: Callable[[TEntity], TResponse] | None = None,
    ) -> None:
        self._model_class = entity_class
        self._response_class = response_class
        self._build_condition = condition_builder
        self._parse_sort = sort_parser if sort_parser is not None else BaseSortParser(entity_class)
        self._map_item: Callable[[TEntity], TResponse] = model_mapper if model_mapper is not None else BaseModelMapper(
            response_class)

    async def execute(self, query: TQuery, scope: TScope) -> Page[TResponse]:
        """
        Execute the search and return a paginated page of response models.

        :param query: Search query defined by the user.
        :param scope: Scope that defines additional filters forced by the application (e.g. authorization filters).
        """
        session = get_sql_session()
        where_conditions = self._build_condition(query, scope)

        stmt = select(self._model_class).where(*where_conditions)
        sort_clauses = query.get_sort_clauses()
        if sort_clauses:
            order_by = self._parse_sort(sort_clauses)
            stmt = stmt.order_by(*order_by)

        offset = query.page * query.page_size
        stmt = stmt.offset(offset).limit(query.page_size)

        total_items = await session.scalar(
            select(func.count()).select_from(self._model_class).where(*where_conditions)
        )
        result: ScalarResult[TEntity] = await session.scalars(stmt)
        items = [self._map_item(item) for item in result.all()]
        return Page.create(
            items=items,
            total=total_items or 0,
            params=query,
        )

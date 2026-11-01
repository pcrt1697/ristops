# ristops-lib-sql

SQLAlchemy async session management.

> Source: [ristops-lib-sql](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-lib-sql/README.md)

## Session management

This module addresses the need to manage SQLAlchemy session lifecycle — open, commit, rollback,
close — without requiring every route handler or service function to do it manually.
`AsyncSqlSessionProvider` owns the engine and session factory and is configured once at startup.
From that point, `@sql_transactional` handles the lifecycle transparently.

Sessions are stored in a `ContextVar`, so each request has its own isolated session. The provider
commits on success and rolls back on any exception.

## Decorator pattern

Two decorators cover the two entry points into the application:

| Decorator | Use case | What it does |
|-----------|----------|-------------|
| `@with_sql_db` | CLI commands | Configures the provider before the command runs |
| `@sql_transactional` | Route handlers, services | Opens a session; reuses the existing one if already open |

`@sql_transactional` uses join-if-exists semantics: if a session is already open in the current
context the function simply joins it, so the outermost call in the stack controls commit and
rollback. This makes it safe to call `@sql_transactional` functions from within other
`@sql_transactional` functions without nesting transactions.

```python
# CLI entry point
@async_command
@with_sql_db
@sql_transactional
async def seed(_: click.Context): ...

# Service layer — safely reuses an open session if one exists
@sql_transactional
async def create_user(data: UserCreate) -> User:
    session = get_sql_session()
    ...
```

## Search execution

This module addresses the need to build paginated, filtered, and sorted list endpoints without
re-writing the same `SELECT … WHERE … ORDER BY … LIMIT/OFFSET` plumbing for every entity.
Two executors share the same shape. `SearchQueryExecutor` takes an entity class, a response model,
and a condition builder, and turns a query object into a plain list of response models; it suits
collections that are always small, such as a venue's services. `PaginatedSearchQueryExecutor` wraps
it, adds offset and limit, and returns a `Page` of response models (running a matching `COUNT` so
the page carries the correct total).

| Constructor argument | Responsibility |
|----------------------|----------------|
| `condition_builder` | Maps the query (and an optional scope) to a list of SQLAlchemy `WHERE` conditions |
| `sort_parser` | Maps `SortClause`s to `ORDER BY` expressions — defaults to `BaseSortParser` (entity columns) |
| `model_mapper` | Maps an ORM entity to its response model — defaults to Pydantic `model_validate` |

Filtering is deliberately generic: the executor only ANDs together whatever conditions the builder
returns. Authorization scoping — "only the venues the user may access" — is therefore just another
condition the caller injects, never something the executor knows about. See the pagination/search
base types in [lib-core](lib-core.md#pagination-and-search).

```python
search_query_executor = SearchQueryExecutor[VenueSearchQuery, VenueSearchScope, VenueEntity, VenueResponse](
    entity_class=VenueEntity,
    response_class=VenueResponse,
    condition_builder=_build_venue_conditions,
)
```

## Schema commands

The `ristops sql-database` command group works from each service's `MODELS` tuple, registered
through the same entry-point mechanism as the other CLI commands:

| Command | Effect |
|---------|--------|
| `generate-ddl <app>` | Prints the SQL DDL for the service's models |
| `create-tables <app>` | Creates the schema and any missing tables; idempotent and non-destructive |
| `nuke <app>` | Drops and recreates the service's tables. Destructive, and it only touches tables still listed in `MODELS` |

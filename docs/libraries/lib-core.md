# ristops-lib-core

Foundation library shared by all backend packages.

> Source: [ristops-lib-core](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-lib-core/README.md)

## Request context

This module addresses the need to make request-scoped data — authenticated user ID, JWT, and
trace IDs — accessible anywhere in the call stack without threading it through every function
parameter. Middleware sets values at the start of each request via `APP_CONTEXT`; any code in
the call chain reads them by key. Standard keys are defined in `ContextKey`: `USER_ID`, `JWT`,
`REQUEST_ID`, `CORRELATION_ID`.

`RequestContextMiddleware` fills the request and correlation IDs. With telemetry enabled they are
the active span's span ID and trace ID, so the correlation ID is the trace ID that follows the
request across services; with it disabled they are generated. Both are echoed back as
`x-request-id` and `x-correlation-id` response headers. Crossing a service boundary is handled by
OpenTelemetry (`traceparent` on HTTP calls) and by `BaseEvent` (on Redis stream messages), not by
this module, so no business code needs to know about it.

## Logging

This module addresses two concerns: attaching request context to every log line, and logging
each HTTP request with its duration and status code.

`RequestContextFilter` is a standard Python logging filter that reads `request_id`,
`correlation_id`, and `user_id` from `APP_CONTEXT` and attaches them to every log record as a
serialised `extras` field. Because it hooks into the logging pipeline rather than individual log
calls, all log lines — including those from third-party libraries — automatically carry the current
request context without any extra effort from the caller.

`RequestLoggingMiddleware` logs a line before and after each request, including the HTTP method,
path, response status code, and elapsed time.

Both the filter class and the formatter class are configurable via `RISTOPS_LOG_FILTER` and
`RISTOPS_LOG_FORMATTER`, so they can be swapped out per service if needed (e.g. to add
service-specific context keys).

## Exception handling

This module standardises error responses across all services. Every error, regardless of its
origin, is returned as the same JSON structure:

```json
{ "title": "Not Found", "detail": "User 123 does not exist" }
```

`GenericExceptionMiddleware` is the outermost layer — it catches any unhandled exception and
returns a 500 rather than leaking a stack trace. Inside that, specific exception types are handled
by registering `BaseHttpExceptionHandler` subclasses with `register_exception_handler`:

```python
register_exception_handler(app, RequestValidationExceptionHandler)  # 422
register_exception_handler(app, GenericHttpExceptionHandler)         # any HTTPException
```

To add a custom handler, subclass `BaseHttpExceptionHandler`, implement `_do_handle`, and
register it the same way.

## Settings

All settings classes extend `BaseServiceSettings`. Settings are loaded from environment variables
with the `RISTOPS_` prefix and from a `.env` file in the working directory.

```python
class MySettings(BaseServiceSettings):
    my_value: str

settings = MySettings.get()  # cached singleton
```

Sub-prefixes by concern:

| Prefix | Owner |
|--------|-------|
| `RISTOPS_` | Core / generic |
| `RISTOPS_LOG_` | Logging |
| `RISTOPS_JWT_` | JWT |
| `RISTOPS_BE_` | Backend service URLs |
| `RISTOPS_PG_` | PostgreSQL |
| `RISTOPS_REDIS_` | Redis |
| `RISTOPS_NEO4J_` | Neo4j |
| `RISTOPS_OTEL_` | Telemetry (see [lib-otel](lib-otel.md)) |

## HTTP client

`HttpClient` wraps a single `httpx.AsyncClient` bound to one downstream service. On every outgoing
request it automatically injects `Authorization: Bearer <jwt>` from `APP_CONTEXT`, so the caller's
identity travels with the call. Trace context is not set here: when telemetry is enabled the httpx
instrumentation adds the W3C `traceparent` header, with no manual wiring.

A service declares one client per downstream dependency and binds them all for the application
lifetime with `with_clients`:

```python
authn_client = HttpClient()
authz_client = HttpClient()

@asynccontextmanager
async def lifespan(_: FastAPI):
    async with with_clients(
        (authn_client, settings.authn_url),
        (authz_client, settings.authz_url),
    ):
        yield
```

Each client exposes its bound `httpx.AsyncClient` via `.client`; using it outside the
`with_clients` context raises. Clients are independent objects, so each domain imports only the
ones it needs rather than reaching into a shared registry.

## Pagination & search

`schema/pagination.py` provides the shared building blocks for list endpoints:

| Type | Purpose |
|------|---------|
| `PaginationParams` | `page` / `page_size` query parameters |
| `SortClause` / `SortDirection` | A parsed sort instruction |
| `SearchQuery` | Base query model — pagination + sort, with filter fields mixed in by a subclass |
| `Page[T]` | A page of results plus `total` / `total_pages` metadata |

A concrete query composes a filter model and declares its sortable fields via a `StrEnum`:

```python
class VenueSearchQuery(SearchQuery, VenueSearchFilter):
    sort_field_enum: ClassVar[type[StrEnum]] = VenueSortField
```

Two conventions make these usable directly as FastAPI query parameters:

- Filter fields are exposed under a `filter.` prefix (`?filter.name=…`) while pagination and sort
  stay bare, via a scoped Pydantic alias generator. This keeps a single combined model (FastAPI
  expands only one query model per endpoint) while preserving the filter grouping.
- `sort_field_enum` is the single source of truth for sortable fields: it both validates the
  submitted `sort` values and feeds the OpenAPI description. Clients pass a repeatable `sort`
  param, prefixing a field with `-` for descending (`?sort=name&sort=-created_at`).

## CLI plugin system

The `ristops` CLI discovers commands and apps via Python entry points. Each package registers
its own commands without modifying a central file:

```toml
[project.entry-points."ristops.cli.commands"]
my-command = "my_package.cli:my_command"

[project.entry-points."ristops.cli.commands.start"]
my-app = "my_package.app:create_app"
```

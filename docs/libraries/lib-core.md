# ristops-lib-core

Foundation library shared by all backend packages.

> Source: [ristops-lib-core](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-lib-core/README.md)

## Request context

This module addresses the need to make request-scoped data — authenticated user ID, JWT, and
trace IDs — accessible anywhere in the call stack without threading it through every function
parameter. Middleware sets values at the start of each request via `APP_CONTEXT`; any code in
the call chain reads them by key. Standard keys are defined in `ContextKey`: `USER_ID`, `JWT`,
`REQUEST_ID`, `CORRELATION_ID`.

It is also the mechanism that ties distributed tracing together: `RequestContextMiddleware` sets
the correlation ID from the incoming request header, `HttpClientService` forwards it to downstream
HTTP calls, and `BaseEvent` carries it into Redis stream messages — all automatically, without any
code in the business layer needing to know about it.

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

## HTTP client

`HttpClientService` wraps `httpx.AsyncClient`. On every outgoing request it automatically
injects `x-correlation-id`, `x-request-id`, and `Authorization: Bearer <jwt>` from
`APP_CONTEXT`, so distributed traces are propagated without any manual wiring.

## CLI plugin system

The `ristops` CLI discovers commands and apps via Python entry points. Each package registers
its own commands without modifying a central file:

```toml
[project.entry-points."ristops.cli.commands"]
my-command = "my_package.cli:my_command"

[project.entry-points."ristops.cli.commands.start"]
my-app = "my_package.app:create_app"
```

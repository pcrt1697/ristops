# ristops-lib-otel

OpenTelemetry instrumentation — traces, metrics and logs, exported over OTLP to a collector.

> Source: [ristops-lib-otel](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-lib-otel/README.md)

## The enabled switch

Everything is gated by `RISTOPS_OTEL_ENABLED` (`TelemetrySettings.enabled`, default `false`), and
disabled is a true no-op: `configure_telemetry` returns immediately, no provider is installed, no
instrumentor patches anything, and no connection to a collector is attempted. A service started
on the host without the flag carries zero telemetry overhead — nothing to opt out of, no JSON to
page through, no dependency on a collector that may not be running.

The flag is per service, which is what makes an incremental rollout possible: two services can
run with telemetry on while the rest stay off, with no shared state between them.

## Usage

Three calls in a service's `create_app()`:

```python
def create_app() -> FastAPI:
    configure_telemetry("be-venue")   # first line: installs the tracer/meter/logger providers
    instrument_clients()              # once per process: httpx, redis, SQLAlchemy

    app = build_api(...)              # the API definition, see ristops-lib-core
    ...
    instrument_app(app)               # last line, after every add_middleware call
    return app
```

`instrument_app` wraps the ASGI app itself — outside every `add_middleware` layer — so a server
span is already active by the time any middleware runs. This is what lets
`RequestContextMiddleware` (`ristops-lib-core`) source `request_id`/`correlation_id` from the
active span (`span_id`/`trace_id`) instead of generating a UUID by hand.

## What auto-instrumentation does not cover

Library-boundary instrumentation (FastAPI, httpx, Redis, SQLAlchemy) produces no domain spans and
does not reach two things in this workspace:

* **Neo4j** — no maintained OTel instrumentation package exists for the driver, so
  `ristops-lib-neo4j`'s `AsyncNeo4jTransactionProvider` opens a `neo4j.transaction` span by hand
  around every transaction, covering every `be-authz` ACL check.
* **Redis Streams** — a trace normally ends at a queue boundary; `ristops-lib-redis` and
  `ristops-lib-be` close it (see their own docs pages).

## Dependencies

`ristops-lib-core`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-grpc`,
`opentelemetry-instrumentation-{fastapi,httpx,redis,sqlalchemy,logging}`

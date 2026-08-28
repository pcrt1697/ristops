# ristops-lib-otel

OpenTelemetry instrumentation: traces, metrics and logs, exported over OTLP to a collector.
Gated entirely by `RISTOPS_OTEL_ENABLED` (default `false`) — a service that doesn't opt in
carries zero telemetry overhead.

[Full documentation](https://pcrt1697.github.io/ristops/#/libraries/lib-otel)

## Usage

In a service's `create_app()`:

```python
configure_telemetry("be-venue")   # first line: installs tracer/meter/logger providers
instrument_clients()              # once per process: httpx, redis, SQLAlchemy
...
instrument_app(app)               # last line, after all middleware is registered
```

## Dependencies

`ristops-lib-core`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-grpc`,
`opentelemetry-instrumentation-{fastapi,httpx,redis,sqlalchemy,logging}`

# Local environment

Two Compose stacks cover the two ways of working on RistOps. Both are defined under `docker/`,
and both work on a clean checkout: every variable has an inline default, so no `.env` file is
required.

> Source: [docker](https://github.com/pcrt1697/ristops/blob/main/docker/README.md)

| File | Run it? | Contents |
|------|---------|----------|
| `docker-compose.local.yaml` | yes — development | Infrastructure and schema creation |
| `docker-compose.yaml` | yes — full stack | Infrastructure, backend services, frontend, observability |
| `docker-compose.infra.yaml` | no | Shared infrastructure definitions |
| `docker-compose.init.yaml` | no | Shared schema creation |

Anything both stacks need is declared once in its own file and pulled into both entry points with
Compose's `include`: the infrastructure containers in one, schema creation in the other. That keeps
a single definition instead of two copies that drift apart. `include` is used rather than YAML
anchors (which cannot cross files) or `extends` (which silently drops `depends_on`).

The split between the two shared files follows their nature rather than their consumers:
`docker-compose.infra.yaml` holds long-running third-party containers with persistent volumes,
while `docker-compose.init.yaml` holds a one-shot task built from this repository's own code.

Both stacks bind the same container names and host ports, so only one can run at a time.

## Full stack

```bash
docker compose -f docker/docker-compose.yaml up -d --build
```

| Endpoint | URL |
|----------|-----|
| Web frontend (nginx) | <http://localhost:5173> |
| bff-web | <http://localhost:8000> |
| be-authn / be-authz / be-venue / be-reservation | <http://localhost:8001> … `:8004` |
| Grafana | <http://localhost:3000> |
| OTLP collector | `localhost:4317` (gRPC), `localhost:4318` (HTTP) |

All five backend services run from a single image built from the uv workspace — they share one
dependency closure, so they differ only by the `ristops start <app>` command and their port. The
frontend is a separate image: Vite builds the static bundle, nginx serves it with an SPA fallback.
Because Vite inlines `VITE_*` variables at build time, the BFF and collector URLs are **build
arguments**, and must be reachable from the browser rather than by Compose service name.

## Development

```bash
docker compose -f docker/docker-compose.local.yaml up -d
```

Applications then run on the host — backend services via `ristops start <app>`, frontend via
`npm run dev`. Stop the Vite dev server before starting the full stack, since both use port 5173.

### Git hooks

The repository uses [pre-commit](https://pre-commit.com). Install the hooks once per clone, from
the repository root:

```bash
pre-commit install
```

The `export-api-schemas` hook regenerates the committed API schemas whenever backend code changes:
the OpenAPI schema of each service (`ristops-backend/packages/<package>/openapi.json`) and the
bff-web GraphQL SDL (`ristops-web/graphql/schema.gql`). It runs `scripts/export-api-schemas.sh`,
which needs no environment or running service. If the hook rewrites a schema, the commit stops:
review the diff, stage the files and commit again.

Run it without committing:

```bash
pre-commit run export-api-schemas --all-files
```

Skipping it (`git commit --no-verify`, or `SKIP=export-api-schemas`) leaves the committed schemas
stale until the next run; there is no other check.

Database schemas are created by the `init-db` one-shot service, which this stack runs too. On a
fresh database, seed the admin user once:

```bash
cd ristops-backend
ristops seed-authz
ristops seed-authn
```

## Initialization

The full stack bootstraps itself with one-shot services that run to completion before the
applications start, gated with `depends_on: service_completed_successfully`. `init-db` is shared
with the development stack, since a fresh database needs its schemas either way; the rest are
specific to the full stack. All of them are
idempotent, so they exit successfully against an already-initialized stack and need no profile
or manual step.

| Service | Responsibility |
|---------|----------------|
| `init-keys` | Generates the ES256 JWT key pair into a named volume, skipping if it already exists |
| `init-db` | Creates the SQL schemas and tables from each service's `MODELS` tuple. Shared with the development stack |
| `seed-authz` | Runs the Neo4j migrations and creates the admin ACL |
| `seed-authn` | Creates the admin user |

The order is not a straight line, because `seed-authn` calls `be-authz` over HTTP to register the
admin as a resource. It therefore runs *after* that service is serving, not before every service:

```text
postgres healthy ──► init-db ─────────────────┐
neo4j healthy    ──► seed-authz ──► be-authz ─┴─► seed-authn ──► be-authn, be-venue,
                                                                 be-reservation, bff-web
```

There is no cycle: `seed-authn` writes to PostgreSQL directly through `@with_sql_db` rather than
calling `be-authn`.

Idempotency comes from the underlying operations rather than from guard flags — Neo4j migrations
are version-tracked, `create_or_update_admin` and `upsert_user` are upserts, and table creation
uses `CREATE SCHEMA IF NOT EXISTS` plus `create_all(checkfirst=True)`.

## Health checks

Every service mounts a shared `health_router` from `ristops-lib-core` at `/health`, outside the
`/api` prefix. It is marked `@public`, so probes bypass both authentication and the
deny-by-default authorization interceptor, and it deliberately checks no downstream dependency:
it answers whether the process can serve requests, not whether the whole stack is well.

## Observability

Applications export OTLP to an OpenTelemetry Collector, which forwards traces, metrics and logs
to `grafana/otel-lgtm` — Loki, Tempo, Prometheus and Grafana bundled in a single container, chosen
over four separate ones to keep the local footprint small.

The applications never speak to a storage backend directly, only OTLP to the collector. The
collector is the single place that knows where telemetry is stored, so replacing Grafana LGTM
with ClickHouse means editing one exporter in `docker/otel/collector-config.yaml` and changing no
application code.

Instrumentation is gated by `RISTOPS_OTEL_ENABLED`, read through `pydantic-settings` like every
other setting. It defaults to `false`, so services started on the host carry no instrumentation
and make no connection attempts to a collector that is not running; the full stack enables it.
Because the flag is per service, instrumentation can be rolled out one service at a time.

All five backend services export traces, metrics and structured logs (`ristops-lib-otel`; see
[lib-otel](libraries/lib-otel.md)). Traces cover the full path — GraphQL operation, HTTP calls
between services (W3C `traceparent`, injected automatically), SQL and Neo4j queries, and Redis
Streams events, which otherwise break a trace at the queue boundary. Grafana is at
<http://localhost:3000> with anonymous admin access; open **Explore** and choose the Tempo, Loki
or Prometheus datasource. `x-correlation-id`/`x-request-id` response headers are the trace ID and
span ID of the request that produced them, pasteable straight into Tempo's search.

## Configuration

Defaults match `ristops-backend/scripts/reset-demo.sh`, so the containerized and host workflows
share one credential set:

| Variable | Default |
|----------|---------|
| `RISTOPS_PG_USER` / `RISTOPS_PG_PWD` / `RISTOPS_PG_DB_NAME` | `ristops` |
| `RISTOPS_REDIS_SESSION_PWD` / `RISTOPS_REDIS_STREAM_PWD` | `ristops` |
| `RISTOPS_NEO4J_PWD` | `ristops1` |
| `RISTOPS_ADMIN_PWD` | `ristops1` |
| `RISTOPS_OTEL_ENABLED` | `true` in the full stack, `false` everywhere else |

Any of them can be overridden from the environment:

```bash
RISTOPS_ADMIN_PWD=secret docker compose -f docker/docker-compose.yaml up -d
```

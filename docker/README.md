# docker

Compose definitions for the local environment. There are two entry points and one
shared file:

| File | Run it? | Contents |
|---|---|---|
| `docker-compose.local.yaml` | yes — development | Infrastructure and schema creation |
| `docker-compose.yaml` | yes — full stack | Infrastructure, backend services, web frontend, observability |
| `docker-compose.infra.yaml` | no | Shared infrastructure definitions, pulled into both via `include` |
| `docker-compose.init.yaml` | no | Shared schema creation, pulled into both via `include` |

Infrastructure and schema creation are each defined once in their own file, so the
two entry points can never drift.

## Development

Infrastructure in containers, applications on the host:

```bash
docker compose -f docker/docker-compose.local.yaml up -d
```

Then run the backend services with `ristops start <app>` and the frontend with
`npm run dev` (port 5173), as documented in each package's `README.md`.

Schemas and tables are created by the `init-db` one-shot service, which both stacks
run. On a fresh database the admin user still has to be seeded once:

```bash
ristops seed-authz
ristops seed-authn
```

## Full stack

Everything in containers, including the observability stack:

```bash
docker compose -f docker/docker-compose.yaml up -d --build
```

| Service | URL |
|---|---|
| Web frontend (nginx) | <http://localhost:5173> |
| bff-web | <http://localhost:8000> |
| be-authn / be-authz / be-venue / be-reservation | <http://localhost:8001> … `:8004` |
| Grafana | <http://localhost:3000> |
| OTLP collector | `localhost:4317` (gRPC), `localhost:4318` (HTTP) |

The two stacks share container names and host ports, so only one can run at a
time. The frontend port is the same in both (5173), served by nginx here and by
the Vite dev server in development — stop the local dev server before starting
this stack, or the two will contend for the port.

## Configuration

Every variable has an inline default, so both stacks come up on a clean checkout
with no `.env` file. The defaults match `ristops-backend/scripts/reset-demo.sh`:

| Variable | Default |
|---|---|
| `RISTOPS_PG_USER` / `RISTOPS_PG_PWD` / `RISTOPS_PG_DB_NAME` | `ristops` |
| `RISTOPS_REDIS_SESSION_PWD` / `RISTOPS_REDIS_STREAM_PWD` | `ristops` |
| `RISTOPS_NEO4J_PWD` | `ristops1` |
| `RISTOPS_ADMIN_PWD` | `ristops1` |
| `RISTOPS_OTEL_ENABLED` | `true` (full stack only) |

Override any of them in the environment, for example:

```bash
RISTOPS_ADMIN_PWD=secret docker compose -f docker/docker-compose.yaml up -d
```

## Initialization

The full stack bootstraps itself through three one-shot services that run before
the applications start. All of them are idempotent, so they exit successfully on
an already-initialized stack:

* `init-keys` — generates the ES256 JWT key pair into the `jwt-keys` volume;
* `init-db` — creates the SQL schemas and tables from each service's models. Shared
  with the development stack, and the replacement for the hand-written
  `postgres/*.sql` scripts that used to duplicate the DDL;
* `seed-authz` — runs the Neo4j migrations and creates the admin ACL;
* `seed-authn` — creates the admin user. It calls `be-authz` over HTTP, so it
  runs *after* that service is healthy rather than before all services.

## Observability

Applications export OTLP to `otel-collector`, which forwards all three signals to
`grafana/otel-lgtm` (Loki, Tempo, Prometheus, Grafana in one container). The
collector is the only place that knows the storage backend, so swapping it means
editing one exporter in `otel/collector-config.yaml`.

Instrumentation is gated by `RISTOPS_OTEL_ENABLED`, which defaults to `false` in
the application settings: services started on the host carry no instrumentation
unless the variable is set explicitly. Being per service, it also allows rolling
telemetry out to one service at a time rather than all five together.

Grafana is at <http://localhost:3000> with anonymous admin access (no login) —
use **Explore** and pick the **Tempo** (traces), **Loki** (logs) or **Prometheus**
(metrics) datasource. `x-correlation-id`/`x-request-id` response headers are the
trace ID and span ID respectively, so either can be pasted straight into Tempo's
search to find the request that produced them.

# RistOps Backend

Python uv workspace containing all backend services and shared libraries.

## Services

| Package                                             | Description                         |
|-----------------------------------------------------|-------------------------------------|
| [be-authn](packages/ristops-be-authn/README.md)     | User management and JWT issuance    |
| [be-authz](packages/ristops-be-authz/README.md)     | ACL, role and permission management |
| [be-venue](packages/ristops-be-venue/README.md)     | Venue registry                      |
| [be-reservation](packages/ristops-be-reservation/README.md) | Reservation config, tables and reservations |
| [bff-web](packages/ristops-bff-web/README.md)       | GraphQL BFF for the web frontend    |
| [batch-demo](packages/ristops-batch-demo/README.md) | Dump demo data                      |

## Libraries

| Package                                                   | Description                                                             |
|-----------------------------------------------------------|-------------------------------------------------------------------------|
| [ristops-lib-core](packages/ristops-lib-core/README.md)   | Shared foundation: context, settings, CLI, HTTP client, auth primitives |
| [ristops-lib-be](packages/ristops-lib-be/README.md)       | Backend-only helpers: auth middleware, stream event base types          |
| [ristops-lib-sql](packages/ristops-lib-sql/README.md)     | SQLAlchemy async session management                                     |
| [ristops-lib-redis](packages/ristops-lib-redis/README.md) | Redis client and stream consumer                                        |
| [ristops-lib-neo4j](packages/ristops-lib-neo4j/README.md) | Neo4j async driver, transactions and migrations                         |
| [ristops-lib-otel](packages/ristops-lib-otel/README.md)   | OpenTelemetry instrumentation: traces, metrics and logs over OTLP       |

## Architecture

```text
browser
  └─► bff-web        (GraphQL + REST, Redis sessions)
        └─► be-authn (user management, JWT — PostgreSQL)
        └─► be-authz (ACL checks — Neo4j)

be-authn ──Redis stream──► be-authz  (user lifecycle events)
any svc  ──Redis stream──► be-authz  (resource lifecycle events)
```

Every service runs the same middleware stack: exception handling, request context
(request/correlation IDs), authentication, request logging. Services other than the BFF validate
JWT tokens by fetching JWKS from `be-authn`. Authorization checks are delegated to `be-authz`
via `AuthZInterceptor`.

## Tech stack

| Concern         | Technology                      |
|-----------------|---------------------------------|
| Language        | Python 3.14                     |
| Framework       | FastAPI                         |
| Auth            | ES256 JWT (PyJWT)               |
| User store      | PostgreSQL via SQLAlchemy async |
| ACL store       | Neo4j                           |
| Sessions        | Redis                           |
| Messaging       | Redis Streams                   |
| BFF API         | Strawberry GraphQL              |
| Validation      | Pydantic v2                     |
| Settings        | pydantic-settings               |
| Package manager | uv workspace                    |

## Package naming conventions

| Prefix   | Used for                                                |
|----------|---------------------------------------------------------|
| `lib-`   | Shared libraries with reusable components               |
| `be-`    | Backend services (business logic or technical services) |
| `bff-`   | Backend-for-frontend services                           |
| `batch-` | Batch services                                          |

## Setup

```bash
uv sync
```

Start the infrastructure the services depend on. This also runs `init-db`, which creates the
SQL schemas and tables, so only the admin user has to be seeded on a fresh database:

```bash
docker compose -f ../docker/docker-compose.local.yaml up -d

ristops seed-authz
ristops seed-authn
```

To create or update the schemas by hand — after adding an entity, for example — run:

```bash
ristops sql-database create-tables be-authn   # and be-venue, be-reservation
```

Each service is started with `ristops start <app>`:

```bash
ristops start be-authn --port 8001
ristops start be-authz --port 8002
ristops start be-venue --port 8003
ristops start be-reservation --port 8004
ristops start bff-web --port 8000
```

See each service's README for the full command with its required environment variables.

To run everything in containers instead — including the frontend and the observability stack —
use the full Compose stack, which builds this workspace into a single image shared by all five
services and seeds itself on startup:

```bash
docker compose -f ../docker/docker-compose.yaml up -d --build
```

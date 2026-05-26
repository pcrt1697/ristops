# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository. This is a training project. I already have experience with some technologies in the
stack, while I'm improving my skills with others.

## Rules

* Do not modify project files without prior approval;
* Explain the reasoning behind all proposed changes;
* Prefer discussing implementation options before writing code;
* Do not execute Git commands, install dependencies, or run migrations unless explicitly requested;
* Markdown files must follow markdownlint rules;
* Python code must follow PEP 8, include type hints on all function signatures, and include
  docstrings on all public classes and functions;

## Repository layout

```text
ristops/
  docker/                  # Docker Compose and infra config (Postgres, Redis x2, Neo4j)
  ristops-backend/         # Python uv workspace (all backend code)
    packages/
      ristops-lib-core/    # Base: FastAPI, Pydantic settings, CLI engine, HTTP client, JWT, context
      ristops-lib-be/      # Backend-only helpers: JwtAuthNMiddleware, AuthZInterceptor, event base types
      ristops-lib-sql/     # SQLAlchemy async session + DDL CLI
      ristops-lib-redis/   # Redis client + stream consumer
      ristops-lib-neo4j/   # Neo4j async driver, transactions, migration engine
      ristops-be-authn/    # Auth backend (users, JWT issuance, PostgreSQL)
      ristops-be-authz/    # AuthZ backend (ACL/roles/resources in Neo4j, Redis stream consumer)
      ristops-bff-web/     # BFF for web (Strawberry GraphQL, Redis sessions)
      ristops-batch-demo/  # Batch processing demo
  ristops-web/             # Frontend (not yet scaffolded)
```

Each package has a `README.md` with its purpose and a link to the full documentation.

## Infrastructure (local)

Start all services with:

```bash
RISTOPS_NEO4J_PWD=ristops1 RISTOPS_PG_PWD=ristops RISTOPS_REDIS_SESSION_PWD=ristops \
RISTOPS_REDIS_STREAM_PWD=ristops \
  docker-compose -f docker/docker-compose.local.yaml up --force-recreate -d
```

| Service       | Port(s)         |
|---------------|-----------------|
| PostgreSQL    | 5432            |
| Redis session | 6379            |
| Redis stream  | 6380            |
| Neo4j         | 7474 (UI), 7687 |

## Backend development

The backend uses [uv](https://github.com/astral-sh/uv) with a workspace.
All commands run from `ristops-backend/`.

```bash
cd ristops-backend

# Install all packages
uv sync

# Seed databases
ristops seed-authn
ristops seed-authz

# Generate SQL DDL for a service
ristops sql-database generate-ddl be-authn

# Run the CLI debugger
python scripts/run_command.py <args>
```

See each service's README for the full start commands with environment variables.

## Settings

All settings use `pydantic-settings` with the `RISTOPS_` prefix. Each settings class inherits
from `BaseServiceSettings` in `ristops-lib-core`. `.env` is loaded from the CWD by default;
override with `RISTOPS_ENV_PATH`. Each package has its own `.env` with service-specific defaults.

Sub-prefixes used by each concern:

| Prefix                  | Owner                    |
|-------------------------|--------------------------|
| `RISTOPS_`              | Core / generic           |
| `RISTOPS_LOG_`          | Logging                  |
| `RISTOPS_JWT_`          | JWT (authn)              |
| `RISTOPS_BE_`           | Backend service URLs     |
| `RISTOPS_PG_`           | PostgreSQL               |
| `RISTOPS_REDIS_`        | Redis (session + stream) |
| `RISTOPS_NEO4J_`        | Neo4j                    |

## Architecture

### Service topology

```text
browser
  └─► bff-web  (GraphQL + REST, Redis session)
        ├─► be-authn  (login, token refresh, user CRUD — PostgreSQL)
        └─► be-authz  (ACL checks, resource/role management — Neo4j)

be-authn ──Redis stream──► be-authz  (user events)
any svc  ──Redis stream──► be-authz  (resource events)
```

### Middleware stack (order of execution, outermost first)

Every FastAPI service uses the same layered middleware. Middlewares are added last-to-first so
the first `add_middleware` call ends up innermost.

1. `GenericExceptionMiddleware` — catches all unhandled exceptions
2. `RequestContextMiddleware` — generates/propagates `x-request-id` and `x-correlation-id`
   into `AsyncContext`
3. `JwtAuthNMiddleware` / `SessionAuthNMiddleware` — validates JWT or session, sets `user_id`
   and `jwt` in context
4. `RequestLoggingMiddleware` — logs request and response with timing

### Authentication & authorization

* `be-authn` issues ES256 JWT access tokens (15 min) and refresh tokens (24 h).
  It exposes `/.well-known/jwks.json`.
* All other services validate tokens by fetching JWKS from `be-authn` via `ClientTokenDecoder`
  (caches keys).
* `be-authz` performs ACL checks via Neo4j. `be-authn` calls `be-authz` for every authorized
  endpoint via `AuthZInterceptor`.
* Mark a route as public (no auth) with the `@public` decorator from
  `ristops_lib_core.auth.authn`.

### CLI plugin system

`ristops-lib-core` implements a plugin-style CLI via Python entry points. Each package declares
its CLI commands under `[project.entry-points."ristops.cli.commands"]` and its startable FastAPI
apps under `[project.entry-points."ristops.cli.commands.start"]` in `pyproject.toml`.
The `ristops start <app>` command discovers registered apps dynamically.

### Inter-service HTTP

`HttpClientService` from `ristops-lib-core` wraps `httpx.AsyncClient`. It automatically injects
`x-correlation-id`, `x-request-id`, and `Authorization: Bearer <jwt>` from the current
`AsyncContext` into outgoing requests, enabling distributed tracing across services.

### Redis streams

`be-authz` consumes two Redis streams (user events, resource events) using
`RedisStreamConsumer`. Producers publish via `RedisStreamProducer`. Consumer groups ensure
at-least-once delivery; stale messages are reclaimed with `XAUTOCLAIM`.

### Database access patterns

* **PostgreSQL** (`be-authn`): SQLAlchemy async sessions via `AsyncSqlSessionProvider`. Decorate
  a route or function with `@sql_transactional` to open a session; if one is already open it is
  reused (join-if-exists). Access the session with `get_sql_session()`. Use `@with_sql_db` on
  CLI entry points to configure the provider before any transactional call.
* **Neo4j** (`be-authz`): same pattern via `@neo4j_transactional`, `get_neo4j_transaction()`,
  and `@with_neo4j_db` for CLI commands.

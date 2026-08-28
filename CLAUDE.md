# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository. This is a training project. I already have experience with some technologies in the
stack, while I'm improving my skills with others.

For area-specific guidance see:

* `ristops-backend/CLAUDE.md` — backend development, settings, architecture
* `ristops-web/CLAUDE.md` — frontend development conventions

## Rules

* Do not modify project files without prior approval;
* Explain the reasoning behind all proposed changes;
* Prefer discussing implementation options before writing/proposing code;
* Do not execute Git commands, install dependencies, or run migrations unless explicitly requested;
* Markdown files must follow markdownlint rules;
* Python code must follow PEP 8, include type hints on all function signatures, and include
  docstrings on all public classes and functions;

## Repository layout

```text
ristops/
  docker/                  # Compose stacks and infra config (see docker/README.md)
    docker-compose.infra.yaml   # shared infra definitions (Postgres, Redis x2, Neo4j)
    docker-compose.init.yaml    # shared one-shot schema creation (init-db)
    docker-compose.local.yaml   # development: infra only, apps run on the host
    docker-compose.yaml         # full stack: infra + services + web + observability
  ristops-backend/         # Python uv workspace (all backend code)
    packages/
      ristops-lib-core/    # Base: FastAPI, Pydantic settings, CLI engine, HTTP client, JWT, context
      ristops-lib-be/      # Backend-only helpers: JwtAuthNMiddleware, AuthZInterceptor, event base types
      ristops-lib-sql/     # SQLAlchemy async session + DDL CLI
      ristops-lib-redis/   # Redis client + stream consumer
      ristops-lib-neo4j/   # Neo4j async driver, transactions, migration engine
      ristops-lib-otel/    # OpenTelemetry instrumentation: traces, metrics, logs over OTLP
      ristops-be-authn/    # Auth backend (users, JWT issuance, PostgreSQL)
      ristops-be-authz/    # AuthZ backend (ACL/roles/resources in Neo4j, Redis stream consumer)
      ristops-be-venue/    # Venue registry (PostgreSQL)
      ristops-be-reservation/  # Reservation config, tables, reservations (PostgreSQL)
      ristops-bff-web/     # BFF for web (Strawberry GraphQL, Redis sessions)
      ristops-batch-demo/  # Batch processing demo
  ristops-web/             # Frontend (React + TypeScript, Vite)
```

Each package has a `README.md` with its purpose and a link to the full documentation.

When a new service is added, the following files must be updated:

* `CLAUDE.md` — repository layout and service topology
* `ristops-backend/README.md` — Services table
* `ristops-backend/packages/<package>/README.md` — create with description, start command,
  dependencies
* `docs/README.md` — Services table (with link)
* `docs/_sidebar.md` — Services navigation list
* `docs/services/<service>.md` — create the service documentation page

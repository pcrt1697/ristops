# RistOps Backend

Python uv workspace containing all backend services and shared libraries.

## Services

| Package | Description |
|---------|-------------|
| [be-authn](packages/ristops-be-authn/README.md) | User management and JWT issuance |
| [be-authz](packages/ristops-be-authz/README.md) | ACL, role and permission management |
| [bff-web](packages/ristops-bff-web/README.md) | GraphQL BFF for the web frontend |
| [batch-demo](packages/ristops-batch-demo/README.md) | Batch processing demo |

## Libraries

| Package | Description |
|---------|-------------|
| [ristops-lib-core](packages/ristops-lib-core/README.md) | Shared foundation: context, settings, CLI, HTTP client, auth primitives |
| [ristops-lib-be](packages/ristops-lib-be/README.md) | Backend-only helpers: auth middleware, stream event base types |
| [ristops-lib-sql](packages/ristops-lib-sql/README.md) | SQLAlchemy async session management |
| [ristops-lib-redis](packages/ristops-lib-redis/README.md) | Redis client and stream consumer |
| [ristops-lib-neo4j](packages/ristops-lib-neo4j/README.md) | Neo4j async driver, transactions and migrations |

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

| Concern | Technology |
|---------|-----------|
| Language | Python 3.14 |
| Framework | FastAPI |
| Auth | ES256 JWT (PyJWT) |
| User store | PostgreSQL via SQLAlchemy async |
| ACL store | Neo4j |
| Sessions | Redis |
| Messaging | Redis Streams |
| BFF API | Strawberry GraphQL |
| Validation | Pydantic v2 |
| Settings | pydantic-settings |
| Package manager | uv workspace |

## Package naming conventions

| Prefix | Used for |
|--------|----------|
| `lib-` | Shared libraries with reusable components |
| `be-`  | Backend services (business logic or technical services) |
| `bff-` | Backend-for-frontend services |

## Setup

```bash
uv sync
```

See each service's README for seed and start commands.

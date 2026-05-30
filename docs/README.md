# RistOps

Backend for a restaurant operations platform. The system manages users, locations, and role-based
access control across multiple services that communicate via HTTP and Redis Streams.

## Services

| Service | Description |
|---------|-------------|
| [be-authn](services/be-authn.md) | User management and JWT issuance |
| [be-authz](services/be-authz.md) | ACL, role and permission management |
| [be-venue](services/be-venue.md) | Venue registry |
| be-reservation | Venue configuration, tables and reservations |
| be-menu | Menus, sections and products |
| be-order | Orders, order items, states and courses |
| [bff-web](services/bff-web.md) | GraphQL BFF for the web frontend |

## Libraries

| Library | Description |
|---------|-------------|
| [ristops-lib-core](libraries/lib-core.md) | Shared foundation: context, settings, CLI, HTTP client, auth primitives |
| [ristops-lib-be](libraries/lib-be.md) | Backend-only helpers: auth middleware, stream event base types |
| [ristops-lib-sql](libraries/lib-sql.md) | SQLAlchemy async session management |
| [ristops-lib-redis](libraries/lib-redis.md) | Redis client and stream consumer |
| [ristops-lib-neo4j](libraries/lib-neo4j.md) | Neo4j async driver, transactions and migrations |

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

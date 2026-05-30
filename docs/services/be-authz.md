# be-authz

Authorization service. Manages ACLs, roles, and permissions in a Neo4j graph and answers
authorization check requests from other services.

> Source: [ristops-be-authz](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-be-authz/README.md)

## Graph model

A graph database is used because authorization requires hierarchy traversal: a user may have
access to a resource not because of a direct ACL entry, but because they have access to a parent
resource. Expressing and querying this in a relational model would require recursive CTEs; in a
graph it is a natural path traversal.

![Authorization data model](../assets/dm-ristops-authr.arrow.png "Authorization data model")

Resources are typed (`app`, `location`, `user`, `role`, `acl`, `permission`) and form a hierarchy
via `BELONGS_TO`. Permission actions: `get`, `list`, `add`, `edit`, `remove`, `*` (manage).

## Authorization check flow

1. A service calls `be-authz` with a `CheckAuthorizationRequest` containing the user ID and the
   required grants (resource + permission pairs)
2. `be-authz` queries Neo4j for a path from the user to an ACL that covers the resource (or any
   ancestor) with a role that grants the permission
3. Returns `is_authorized: true/false`

The check is performed by `AuthZInterceptor` before every non-public request. Because the
check is centralised here, adding a new resource type or changing a role's permissions requires
no changes in the calling services.

## Stream consumers

Rather than coupling `be-authz` to `be-authn` via a direct API call, user and resource lifecycle
events are published to Redis Streams. This keeps the services independent and makes the sync
resilient to temporary downtime — messages are replayed when the consumer recovers.

| Stream | Event | Action |
|--------|-------|--------|
| User stream | `created` | Creates a `User` node and a default member ACL |
| User stream | `deleted` | Removes the `User` node and all related ACLs |
| Resource stream | `created` | Creates `Resource` nodes with optional parent link |
| Resource stream | `deleted` | Removes the `Resource` node |

## Migrations

Schema and data changes are applied via `.cypher` files in
`src/ristops_be_authz/database/migrations/`, run in order by the `seed-authz` command.
Each applied migration is tracked as a `Migration` node in the graph. See
[ristops-lib-neo4j](../libraries/lib-neo4j.md) for the migration engine details.

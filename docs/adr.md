# ADRs

Architectural decisions for the RistOps project.

---

## General

### Monorepo

**Context:** The project has multiple backend packages and a frontend that share utilities,
and no intent to publish packages to a public or private registry.

**Decision:** Use a single monorepo for all code.

**Why:** Shared libraries work without a registry, cross-package refactoring is atomic,
and the CI pipeline stays unified.

**Status:** Accepted

---

## Backend

### Microservices over monolith

**Context:** The backend covers distinct concerns — authentication, authorization, and
frontend aggregation — each with different storage backends and different expected
scaling profiles. This is also a training project designed to practice distributed systems
patterns.

**Decision:** Split the backend into focused microservices rather than a single monolith.

**Why:** Each service has a clear bounded context; `be-authn` owns user identity,
`be-authz` owns access control, `bff-web` owns frontend aggregation. The separation
allows each to evolve and scale independently.

**Trade-off:** Higher operational complexity for a single developer. Acceptable here
because the explicit goal is learning those patterns.

**Status:** Accepted

---

### Python + FastAPI

**Context:** A high-productivity async web framework is needed for the backend services.

**Decision:** Python with FastAPI.

**Why:** FastAPI is one of the most widely adopted async Python frameworks, has excellent
Pydantic integration, and auto-generates OpenAPI docs. Python is well suited to the team's
existing skill set.

**Status:** Accepted

---

### BFF pattern

**Context:** The frontend has different query needs than the core APIs, and a future mobile
client is a possibility.

**Decision:** Introduce a Backend-for-Frontend (`bff-web`) that sits between the frontend
and the backend services.

**Why:** Keeps core APIs clean and stable. Aggregation, reshaping, and frontend-specific
concerns are isolated to the BFF. Adding a mobile BFF later does not require touching
core services.

**Status:** Accepted

---

### GraphQL for the BFF, REST for auth endpoints

**Context:** The BFF needs a flexible query interface; authentication follows well-known
standards.

**Decision:** The BFF exposes a GraphQL API (Strawberry). Authentication endpoints
(`/login`, `/refresh`, etc.) are REST.

**Why:** GraphQL lets the frontend fetch exactly what it needs without over-fetching.
REST is more standard for auth flows and maps naturally to HTTP semantics
(e.g., `401 Unauthorized`).

**Status:** Accepted

---

### REST between backend services (for now)

**Context:** Backend services need to call each other synchronously.

**Decision:** Use REST (HTTP/JSON) for inter-service communication.

**Why:** Simple to implement and debug. Acceptable performance for current needs.

**Trade-off:** gRPC may be adopted for performance-critical services in the future
(strongly typed contracts, binary framing, streaming).

**Status:** Accepted — provisional, gRPC migration possible

---

### Shared Pydantic models for cross-cutting service contracts

**Context:** This is a training project in a monorepo. Inter-service communication requires
a shared understanding of data shapes. Three approaches were evaluated:

- **Shared Pydantic models** — single source of truth, consumer-side validation included,
  coupling across services.
- **Autonomous models per service** — each service defines its own request/response types;
  consumer models are intentionally narrow (tolerant reader). No shared code, but contracts
  can drift silently.
- **TypedDict contracts shared, Pydantic models in the owning service** — type safety via
  static analysis without runtime validation on the consumer. Discarded because TypedDict
  is structurally invisible at runtime: a mismatched response produces a generic error deep
  in business logic rather than a clear failure at the HTTP boundary.

**Decision:** Shared Pydantic models in `lib-core` are used only for contracts that are
genuinely cross-cutting — infrastructure services that every other service depends on
(authentication, authorisation). Business domain service contracts stay inside their owning
service.

**Why:** The monorepo makes sharing straightforward, removing the usual distribution
overhead (no registry, atomic refactoring). In a monorepo, shared models are a pragmatic
default — the coupling in the code reflects the coupling that already exists in the
architecture.

The scope limit to infrastructure services is intentional: their contracts are inherently
cross-cutting and change rarely and deliberately. A change to an infrastructure contract
affects all consumers by definition, so tight coupling is a correct reflection of reality.
Business domain contracts do not share this property — they should be free to evolve
independently, so autonomous models are the right choice there.

**Trade-off:** Consumers re-validate data already validated by the producer. Accepted
because infrastructure contracts are stable and the validation provides a clear failure
mode at the boundary.

**Status:** Accepted

---

### Session authentication for the BFF, JWT for backend services

**Context:** Frontend users need a convenient auth mechanism; backend services must
authenticate requests without shared state.

**Decision:** The BFF manages Redis-backed sessions for frontend users. All backend
services use JWT (stateless).

**Why this is not an anti-pattern:** Sessions are fully contained within the BFF boundary.
Backend services are stateless — they never see or manage sessions. This gives the
frontend a standard session UX while keeping core APIs clean and decoupled.
The BFF performs session validation and then forwards the JWT inward.

**Status:** Accepted

---

### Zero-trust between backend services

**Context:** Backend services call each other over an internal network.

**Decision:** Apply zero-trust: every inter-service request is authenticated and authorized,
regardless of network origin.

**Why:** Delegating authentication and authorization to individual services avoids placing
that responsibility in the BFF. If the BFF were the only auth enforcement point, every
new backend service would require BFF changes. Zero-trust also limits blast radius if one
service is compromised.

**Status:** Accepted

---

### PostgreSQL for transactional data

**Context:** `be-authn` needs a reliable store for user records and credentials.

**Decision:** PostgreSQL via SQLAlchemy async.

**Why:** Industry-standard relational database, well suited for transactional operations,
strong consistency guarantees, mature async driver support in Python.

**Status:** Accepted

---

### Neo4j for the authorization service

**Context:** `be-authz` implements a ReBAC model with hierarchical resources, roles,
and relationships.

**Decision:** Neo4j as the primary store for `be-authz`.

**Why:** Graph databases are a natural fit for relationship-based access control.
Hierarchical queries (e.g., "does this user have permission on any ancestor of this
resource?") that are expensive in SQL are first-class operations in Cypher.

**Status:** Accepted

---

### ReBAC authorization model

**Context:** The system needs to express access rules that depend on relationships between
users, roles, and resources — not just flat role assignments.

**Decision:** Use Relationship-Based Access Control (ReBAC).

**Why:** RBAC is too coarse for hierarchical resource ownership and relationship-based
rules. PBAC is more expressive but too complex to maintain at this scale.
ReBAC is the right trade-off: expressive enough for ownership hierarchies,
simpler to reason about than full policy engines.

**Status:** Accepted

---

### Deterministic ACL identity (one ACL per user / resource / role)

**Context:** An ACL grant links a user to a resource with a role
(`(:User)-[:HAS_ACCESS]->(:Acl)-[:ON]->(:Resource)` and `(:Acl)-[:WITH_ROLE]->(:Role)`).
The original implementation gave each `Acl` a random `uuid4` and `MERGE`d the access path
keyed only on `(user, resource)`. The role was outside the merge key, so granting a second
role on the same resource reused the existing `Acl` node (attaching multiple `WITH_ROLE`
relationships) and the `ON CREATE` clause overwrote the node id. There was no database-level
guarantee of a single ACL per `(user, resource, role)` tuple.

**Decision:** Derive the `Acl` id deterministically from the tuple —
`uuid5(namespace, "{user_id}|{resource_type}|{resource_id}|{role_id}")` — and `MERGE` on
`(:Acl {id})`, then `MERGE` each relationship individually. The pre-existing
`acl_id IS UNIQUE` constraint then enforces one ACL per tuple.

**Why:** A natural-key id turns the existing uniqueness constraint into tuple-level
enforcement at the database, prevents roles from collapsing onto a shared node, and gives both
grant and revoke an unambiguous target (the node with the recomputed id) with no traversal.
Because creating an existing grant now writes nothing, grant can detect the duplicate from the
query counters and reject it with `409 Conflict` (and revoke likewise returns `404` when the
target ACL is absent) — the response always reflects what actually changed.

**Trade-off:** The id is no longer opaque — it is a pure function of the grant tuple.
Acceptable: the tuple is the natural identity of a grant, and a reproducible id is shared
cleanly between grant and revoke.

**Status:** Accepted

---

### Redis Streams for async service-to-service messaging

**Context:** Services need to publish and consume events asynchronously
(e.g., user lifecycle events from `be-authn` to `be-authz`).

**Decision:** Redis Streams with consumer groups.

**Why not Redis Pub/Sub:** Pub/Sub does not support consumer groups or stale-message
reclaim (`XAUTOCLAIM`). Both are required for reliable at-least-once delivery,
particularly when service replicas are introduced.

**Status:** Accepted

---

### Redis Strings for session storage

**Context:** The BFF needs fast, ephemeral storage for user sessions.

**Decision:** Redis Strings (key/value) on a dedicated Redis instance.

**Why:** Simple data model, TTL-based expiry aligns with session lifetime,
sub-millisecond reads.

**Status:** Accepted

---

### Two Redis instances

**Context:** Sessions and streams have fundamentally different durability requirements.

**Decision:** Run a dedicated Redis instance for sessions and a separate one for streams.

**Why:** The two workloads need different memory eviction policies.
Sessions use `allkeys-lru`: eviction is acceptable — a lost session just forces
re-login. Streams use `noeviction`: messages must not be silently dropped,
so the instance should reject writes rather than evict data when memory is full.
Mixing both workloads on one instance would force a compromise on eviction policy.

**Status:** Accepted

---

### uv as package manager

**Context:** The backend is a multi-package Python workspace.

**Decision:** `uv` with workspace support.

**Why:** Native workspace support, significantly faster than `pip`/`poetry`,
and produces a deterministic lockfile suitable for reproducible builds.

**Status:** Accepted

---

### ES256 JWT signing

**Context:** Multiple services need to verify JWT tokens issued by `be-authn`.

**Decision:** Sign tokens with ES256 (asymmetric ECDSA keys).

**Why:** Any service can verify tokens by fetching the public key from `be-authn`'s
JWKS endpoint (`/.well-known/jwks.json`) without sharing a secret.
Access tokens expire after 15 minutes; refresh tokens after 24 hours —
a standard trade-off between usability and exposure window.

**Status:** Accepted

---

### Plugin-based CLI via entry points

**Context:** Multiple packages contribute commands to the `ristops` CLI.

**Decision:** Use Python entry points (`[project.entry-points."ristops.cli.commands"]`)
to register commands from each package.

**Why:** Keeps the CLI extensible without coupling `ristops-lib-core` to individual
services. New packages self-register; the core discovers them dynamically.

**Status:** Accepted

---

### AsyncContext for correlation ID propagation (temporary)

**Context:** `x-request-id`, `x-correlation-id`, and the JWT need to flow through all
service layers without being threaded through every function signature.

**Decision:** Use `AsyncContext` (contextvars-based) to propagate these values implicitly.
`HttpClientService` reads from context and injects headers into outgoing requests
automatically.

**Why temporary:** This is a workaround until the Elastic stack is integrated for
distributed tracing, possibly via OpenTelemetry. At that point, trace context propagation
will be handled by the OTel SDK and the `AsyncContext` mechanism can be retired.

**Status:** Accepted — provisional, OTel migration planned

---

## Domain services

### `be-reservation` is a single deployable with a single database

**Context:** Venue configuration (opening times, services, slot duration, reservable seats,
closures, exceptions), tables, and reservations are all required to answer "is this slot
available?". That check must be atomic — it is the foundation of the double-booking
prevention strategy.

**Decision:** Single service, single DB (`be-reservation`). Module boundaries in code,
not service boundaries.

**Why:** Splitting config, tables, and reservations across services would turn a DB
transaction into a distributed coordination problem. The atomic `INSERT WHERE` that
prevents double-booking is impossible across service boundaries.

**Status:** Accepted

---

### Reservation config is a separate concern within `be-reservation`

**Context:** The restaurant needs to configure opening times, services (lunch/dinner),
slot duration, reservable seats, closures, and per-date exceptions. This config is required
to compute availability, so it must live in the same DB as reservations. However, it serves
a fundamentally different purpose — it is the rule set, not the operational data.

**Decision:** Config is split into two layers:

- `ServiceConfig` — base rules (opening times, slot duration, weekdays)
- `DayOverride` — per-date exceptions (closures, modified hours, special events)

Slots are never stored; they are computed from these two layers at query time.

**Why:** Separating config from reservations means operational data never needs to change
when rules change. The override model keeps exceptions from polluting the base config.
Extracting config to a separate service would reintroduce the distributed coordination
problem that the previous decision explicitly avoids.

**Status:** Accepted

---

### Menu and orders are separate services from reservation

**Context:** `be-menu` and `be-order` were candidates for co-location with `be-reservation`.
Their relationship to reservation is fundamentally different from the relationship between
reservation and its config.

**Decision:** `be-menu` and `be-order` are separate deployables with separate databases.
Integration is event-driven.

**Why:** After an order line is created (with a snapshotted price and product name), the
menu service is no longer needed to serve that order. The coupling is transient, not
operational. Eventual consistency is acceptable here — which is the opposite of the
reasoning that keeps reservation and its config co-located.

**Status:** Accepted

---

### `be-venue` is a standalone service acting as the location registry

**Context:** Every domain service (`be-reservation`, `be-menu`, `be-order`) needs a root
reference to identify which venue it is operating on. Without a central owner, venue IDs
would be unvalidated magic UUIDs with no lifecycle management — making it impossible to
later enable/disable venues, enforce existence, or add venue-level metadata.
Staff assignment is not a venue concern; it is handled by `be-authz` via ACL rules on
venue resources.

**Decision:** `be-venue` is a dedicated deployable that owns the venue registry. Other
services reference venue IDs issued by `be-venue` but do not call it on hot paths.

**Why not encapsulate it inside `be-reservation`:** Venues are a cross-cutting concern
shared by reservation, menu, and order. Co-locating the registry inside one domain service
would create an implicit dependency from the others on that service for a concern unrelated
to their core responsibility.

**Trade-off:** Adds an additional service to operate. Acceptable because `be-venue` is expected
to be thin and low-traffic; establishing a canonical venue identity from the start avoids
a retro-fit across all other services later.

**Status:** Accepted

---

### Kitchen display is part of `be-order`, not a separate service

**Context:** The kitchen display was considered as a separate read service for showing
and updating order statuses.

**Decision:** Kitchen is a role-scoped interface within `be-order`, not a separate
deployable.

**Why:** A service that is operationally useless when its dependency is down provides
false resilience. The kitchen and orders are in the same failure domain regardless of
whether they are split. Splitting adds operational complexity without any resilience benefit.

**Status:** Accepted

---

## Frontend

> This section will be expanded when frontend development begins.

### React

**Context:** A frontend framework is needed for `ristops-web`.

**Decision:** React.

**Why:** Widely adopted, integrates naturally with GraphQL clients (Apollo, urql),
and familiar to the team.

**Status:** Accepted

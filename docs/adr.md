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

## Frontend

### React

**Context:** A frontend framework is needed for `ristops-web`.

**Decision:** React.

**Why:** Widely adopted, integrates naturally with GraphQL clients (Apollo, urql),
and familiar to the team.

**Note:** This section will be expanded when frontend development begins.

**Status:** Accepted

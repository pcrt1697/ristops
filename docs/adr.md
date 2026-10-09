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

**Context:** The backend covers distinct concerns — authentication, authorization, the venue
registry, reservations, and frontend aggregation — each with different storage backends and
different expected scaling profiles. This is also a training project designed to practice distributed systems
patterns.

**Decision:** Split the backend into focused microservices rather than a single monolith.

**Why:** Each service has a clear bounded context; `be-authn` owns user identity,
`be-authz` owns access control, `be-venue` owns the venue registry, `be-reservation` owns
schedules and bookings, `bff-web` owns frontend aggregation. The separation allows each to
evolve and scale independently.

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

**Context:** `be-authn`, `be-venue` and `be-reservation` need a reliable store for transactional
records — users and credentials, venues, schedules and bookings.

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

### Time-bounded ACL grants (`expires_at`)

**Context:** Some access is inherently temporary — trial/probation staff, contractors,
delegated access. The ReBAC model is purely additive (grants + wildcards + downward
inheritance) with no deny mechanism, so "revoke access after a date" cannot be expressed by
grants alone, especially when the access is inherited from an ancestor resource.

**Decision:** Add an optional `expires_at` timestamp to the `Acl` node. A grant whose
`expires_at` is in the past is treated as absent. Every authorization *and* listing query
filters expired grants with `(acl.expires_at IS NULL OR datetime(acl.expires_at) > datetime($now))`.
`expires_at` is set on every grant (not only `ON CREATE`), so re-granting the same
(user, resource, role) updates the expiry. Expired nodes are left in place and filtered at
query time rather than actively purged.

**Why:** Time-bounding is the additive-model-friendly way to express temporary access — an
expired grant simply stops counting, with no deny layer. Filtering at read time keeps
correctness without requiring a background cleanup job.

**Trade-off:** The filter must be applied in *every* ACL-traversing query (the authorization
check and all listings); missing one silently leaks access. Timestamps are compared via Neo4j
`datetime()` rather than lexicographic string comparison, to avoid format-dependent bugs.
Expired nodes linger until re-granted or cleaned up (housekeeping only, not correctness).

**Status:** Accepted

---

### Role assignment scope

**Context:** Roles are global nodes granted on resources. Some roles only make sense on
certain resource types — venue roles (owner, manager) must not be assignable to `app/*`, and
app roles (admin, developer) must not be assignable to a venue. Nothing prevented a
nonsensical or dangerous assignment (e.g. a venue role granted at app level).

**Decision:** Add a single `scope: ResourceType` field to each role declaring the resource
type it may be assigned to. `grant_access` rejects a grant whose resource type ≠ the role's
scope, and `listRoles` accepts a `scope` filter so the assign UI only offers roles valid for
the target resource. Existing roles: `admin`/`developer` → `app`, `member` → `user` (it is
auto-granted on each user's own `USER` resource), venue roles → `venue`.

**Why a single scope, not a list:** access inherits downward via `BELONGS_TO`, so a role is
granted at its canonical level (e.g. a venue role on the venue) and cascades to sub-resources
automatically — there is no need to assign the same role at multiple levels. App-wide variants
are modelled as separate app-scoped roles. A single scope is sufficient and forward-compatible:
widening to a list later is a non-breaking change.

**Enforcement:** validated server-side in `grant_access`, not only filtered in the frontend,
so a crafted request cannot assign a role outside its scope.

**Note:** a role's *scope* (which resource type it attaches to) is a different concept from a
*permission's* scope (the prefix before `:` in an id like `venue:add`).

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

### AsyncContext for request-scoped values

**Context:** The user ID, the JWT, and the request and correlation IDs need to flow through all
service layers without being threaded through every function signature.

**Decision:** Use `AsyncContext` (contextvars-based) to carry them implicitly. Middleware fills
it for each request, `HttpClient` reads the JWT from it to set the `Authorization` header on
outgoing calls, and the logging filter attaches the IDs to every log record.

**Why:** Business code stays free of plumbing. Trace propagation is not part of this mechanism:
with OpenTelemetry the request ID is the span ID and the correlation ID is the trace ID, and
`traceparent` crosses HTTP and Redis boundaries through instrumentation and `BaseEvent`. With
telemetry disabled the IDs are generated, so nothing depends on it.

**Status:** Accepted

---

### OpenTelemetry through a collector, with Grafana LGTM

**Context:** A request crosses several services and sometimes a Redis stream, and hand-propagated
correlation headers could not show where time was spent or follow a trace over a queue.

**Decision:** Services export traces, metrics and logs over OTLP to an OpenTelemetry Collector,
which forwards them to `grafana/otel-lgtm` (Loki, Tempo, Prometheus and Grafana in one
container). Instrumentation is switched per service by `RISTOPS_OTEL_ENABLED`, off by default.

**Why:** The collector is the only component that knows where telemetry is stored, so replacing
Grafana LGTM with another backend changes one exporter and no application code. One bundled
container keeps the local footprint small. The per-service flag allows an incremental rollout and
leaves host development with no overhead and no dependency on a running collector.

**Trade-off:** Two boundaries are not covered by library instrumentation and need code of our own:
Neo4j transactions (a span opened by hand) and Redis Streams (a `traceparent` carried in the event
payload).

**Status:** Accepted

---

## Domain services

### `be-reservation` is a single deployable with a single database

**Context:** Venue configuration (services, their openings and closings) and reservations are
all required to answer "can this booking be accepted?". That check must be atomic — it is the
foundation of the overbooking prevention strategy.

**Decision:** Single service, single DB (`be-reservation`). Module boundaries in code,
not service boundaries.

**Why:** Splitting config and reservations across services would turn a DB transaction into a
distributed coordination problem. The capacity check and the insert must run under one lock
(`SELECT ... FOR UPDATE` on the service being booked), which is impossible across service
boundaries.

**Status:** Accepted

---

### Reservation config is a separate concern within `be-reservation`

**Context:** The restaurant needs to configure opening times, services (lunch/dinner),
reservable seats, and closures. This config is required to compute availability, so it must
live in the same DB as reservations. However, it serves a fundamentally different purpose —
it is the rule set, not the operational data.

**Decision:** Config lives in its own modules within `be-reservation`, never in a separate
service. Availability is computed from it at query time and never stored.

**Why:** Separating config from reservations means operational data never needs to change
when rules change. Extracting config to a separate service would reintroduce the distributed
coordination problem that the previous decision explicitly avoids.

**Status:** Accepted — the two-layer `ServiceConfig`/`DayOverride` shape this entry originally
prescribed is superseded by the entry below.

---

### One-off services replace schedule overrides

**Context:** Configuration had grown four layers of exceptions — base openings, opening
overrides, capacity overrides, and closings — resolved in precedence order at query time. The
layers needed a cross-service overlap engine to keep a booking's service unambiguous, since a
reservation carried no service reference and was matched to one by wall-clock time. That engine
was the single largest piece of logic in the service, and the layers had to be surfaced in the UI
for a user to predict what any given date would do.

**Decision:** Collapse the model to three concepts:

- `Service` — a validity date range plus a seat capacity
- `Opening` — the hours it runs on one weekday
- `Closing` — a date range removing one or more services from the calendar

An exception is expressed as *another service*, bounded to the dates it applies to, paired with a
closing on the service it replaces. Reservations gain a `service_id`, so a booking names its
service instead of being matched to one. Turn duration, slot interval, advance notice and grace
period are dropped: a booking may sit at any minute inside its service's window, and capacity is
counted per service per business date.

**Why:** A one-off service is the same concept a user already understands, applied to a narrower
date range — it needs no precedence rules to explain. Storing the service on the booking removes
the reason the overlap check had to be exhaustive: it survives now only to keep a venue's schedule
readable, and reduces to comparing weekday windows and looking for a date both services actually
run. Counting capacity per service, rather than as peak concurrency over rolling turn windows,
makes the number staff see the one the rule enforces.

**Trade-off:** A recurring exception costs one service per occurrence rather than one row (a
weekday-scoped seasonal change, for instance, has no single-row equivalent), and a closing cannot
be shrunk or deleted when doing so would re-expose an overlap it was hiding. Both are accepted in
exchange for a model with no precedence order to learn.

**Status:** Accepted

---

### Schedule changes never rewrite existing reservations

**Context:** Editing a schedule — shrinking hours, closing a date, lowering capacity, retiring a
service — can invalidate bookings that were valid when they were made.

**Decision:** Schedule edits mutate nothing on reservations. Each future booking in a live status
is checked against the current schedule when read and flagged with a violation (`no_service`,
`closed`, `outside_hours`). Staff resolve it by hand, either with the `withdraw` action — a status
distinct from the customer's `canceled` and the venue's pre-acceptance `rejected` — or by moving
the booking to another service. Capacity overflow is reported on the calendar rather than blamed
on one booking.

**Why:** Auto-cancelling would drop a guest's booking silently, with no notification. Reverting to
`pending` loses the "confirmed" state and does not fix the invalidity. Blocking the edit is too
rigid: a venue could not close for a holiday until every booking was resolved by hand.

**Trade-off:** Violations are computed on every read against an in-memory snapshot of the venue's
schedule instead of being stored, so they never go stale, at the cost of that computation and of
staff having to act manually.

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

### React, TypeScript and Vite

**Context:** A frontend framework is needed for `ristops-web`.

**Decision:** React with TypeScript, built with Vite.

**Why:** Widely adopted, and strong typing carries through to the generated GraphQL types. Vite
gives a fast development server and a static bundle that nginx serves with an SPA fallback.

**Status:** Accepted

---

### Ant Design for UI components

**Context:** The interface is an operations tool: tables, forms, modals, drawers and date pickers.

**Decision:** Use Ant Design (antd).

**Why:** It ships the data-heavy components out of the box, so effort goes into domain behaviour
rather than building primitives.

**Trade-off:** Look and bundle size are tied to the library.

**Status:** Accepted

---

### TanStack Query over graphql-request, not a full GraphQL client

**Context:** The BFF is the only GraphQL endpoint the frontend talks to. Full clients such as
Apollo or urql bring a normalized cache and their own state model.

**Decision:** Server state is handled by TanStack Query, with requests made through
`graphql-request`. Raw requests live in each domain's `*.api.ts`; components consume per-domain
`use*` hooks.

**Why:** Query-key caching and invalidation are enough for this app, and the same mechanism serves
the REST calls to the BFF, such as authentication. A normalized cache would add concepts without a
need for them.

**Trade-off:** No automatic cache normalization, so mutations invalidate the affected queries
explicitly.

**Status:** Accepted

---

### Types generated from the BFF schema

**Context:** The frontend and the BFF share a contract that changes whenever a resolver changes.

**Decision:** GraphQL operations are written in `.graphql` files colocated per domain. The BFF
exports its schema as SDL, and graphql-codegen produces typed documents from both. The generated
files are never edited by hand.

**Why:** A schema change surfaces as a compile error in the frontend instead of a runtime failure.

**Status:** Accepted

---

### Frontend code is organized by domain

**Context:** A layer-first layout (all hooks together, all API calls together) scatters one change
across the tree.

**Decision:** Each domain folder holds its own API, hooks, types and helpers. Code moves to a
shared location only when it is genuinely generic.

**Why:** Colocation keeps a change to one domain in one place and makes a domain easy to find.

**Status:** Accepted

---

### Permissions gate the UI, the backend enforces them

**Context:** Users should not be offered actions they cannot perform, but a client cannot be
trusted to enforce access.

**Decision:** The UI hides or disables actions based on the user's grants (`useCan`,
`RequirePermission`). Every endpoint remains protected by the backend, which stays the only
enforcement point.

**Why:** A better experience without moving trust to the client, consistent with the zero-trust
decision for the backend.

**Trade-off:** Permission knowledge exists in two places, and a stale UI can offer an action the
backend then rejects.

**Status:** Accepted

---

### Current venue is client state, persisted in localStorage

**Context:** Most of the app works inside one venue, and a page reload must not forget which.

**Decision:** The selected venue lives in a React context under `domain/venue`, persisted in
`localStorage` and kept in sync with the `/venues/:venueId` route. Server-side user preferences are
deferred.

**Why:** A UI preference needs no backend round trip, and the route stays the source of truth when
a venue is opened by link.

**Trade-off:** The choice is not shared between devices.

**Status:** Accepted

---

### REST bodies are snake_case, GraphQL is camelCase

**Context:** The BFF exposes both: GraphQL (Strawberry, camelCase) and REST for authentication,
whose Pydantic bodies are snake_case.

**Decision:** The frontend sends snake_case in REST bodies and camelCase in GraphQL operations. It
adapts to the backend contract; the backend does not add alias generators to suit the frontend.

**Why:** The backend owns the contract, and each protocol keeps its own convention.

**Status:** Accepted

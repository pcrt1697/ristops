# CLAUDE.md — backend

Guidance for the Python backend (`ristops-backend`). Repo-wide rules and layout live in the
root `CLAUDE.md`.

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

# Export the OpenAPI schema of a service (no environment needed)
ristops openapi export be-reservation -f packages/ristops-be-reservation/openapi.json -o

# Generate SQL DDL for a service
ristops sql-database generate-ddl be-authn

# Create the schema and any missing tables (idempotent, non-destructive)
ristops sql-database create-tables be-authn

# Reset a database (DESTRUCTIVE, schema only — reseed separately)
ristops sql-database nuke be-authn   # drop + recreate tables (SQL services)
ristops nuke-authz                   # delete all nodes (authz/Neo4j)

# Run the tests (a package's tests directory is run on its own: its conftest.py and helpers.py are not namespaced)
pytest packages/ristops-lib-core/tests

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
| `RISTOPS_OTEL_`         | Telemetry (`ristops-lib-otel`) |

## Architecture

### Service topology

```text
browser
  └─► bff-web  (GraphQL + REST, Redis session)
        ├─► be-authn   (login, token refresh, user CRUD — PostgreSQL)
        ├─► be-authz   (ACL checks, resource/role management — Neo4j)
        ├─► be-venue   (venue registry — PostgreSQL)
        └─► be-reservation  (reservation config, tables, reservations — PostgreSQL)

be-authn   ──Redis stream──► be-authz         (user events)
any svc    ──Redis stream──► be-authz         (resource events)
be-venue   ──Redis stream──► be-reservation   (venue events — local read-model sync)
be-venue   ──HTTP──────────► be-reservation   (venue activation: at least one service required)
other svcs ──HTTP──────────► be-authn         (JWKS fetch, to verify JWTs locally)
authn, venue, reservation ──HTTP──► be-authz  (ACL check on every authorized request)
```

### Middleware stack (order of execution, outermost first)

Every FastAPI service uses the same layered middleware. Middlewares are added last-to-first so
the first `add_middleware` call ends up innermost. Outermost of all is FastAPI instrumentation
itself (`ristops_lib_otel.instrument_app`, a no-op when `RISTOPS_OTEL_ENABLED` is unset) — it
wraps the ASGI app, so a server span is already active by the time any of the middleware below
runs.

1. `GenericExceptionMiddleware` — catches all unhandled exceptions
2. `RequestContextMiddleware` — sets `request_id`/`correlation_id` in `AsyncContext` from the
   active span (`span_id`/`trace_id`) and mirrors them onto `x-request-id`/`x-correlation-id`,
   falling back to a generated UUID with no active span (telemetry disabled)
3. `JwtAuthNMiddleware` / `SessionAuthNMiddleware` — validates JWT or session, sets `user_id`
   and `jwt` in context
4. `RequestLoggingMiddleware` — logs request and response with timing, `[BEFORE]`/`[AFTER]`. This
   was dropped during the OTel rollout on the assumption that the FastAPI instrumentation's server
   span made it redundant — it doesn't, for `docker logs`/host stdout, which isn't Tempo. Kept
   alongside tracing rather than instead of it.

### Authentication & authorization

* `be-authn` issues ES256 JWT access tokens (15 min) and refresh tokens (24 h).
  It exposes `/.well-known/jwks.json`.
* All other services validate tokens by fetching JWKS from `be-authn` via `ClientTokenDecoder`
  (caches keys).
* `be-authz` performs ACL checks via Neo4j. `be-authn` calls `be-authz` for every authorized
  endpoint via `AuthZInterceptor`.
* Mark a route as public (no auth) with the `@public` decorator from
  `ristops_lib_core.auth.authn`.
* Every service mounts the shared `health_router` from `ristops_lib_core.app.health` at
  `/health` (outside `/api`). It is `@public`, so container probes need neither a token nor a
  `@policy`, and it deliberately checks no downstream dependency.

### CLI plugin system

`ristops-lib-core` implements a plugin-style CLI via Python entry points. Each package declares
its CLI commands under `[project.entry-points."ristops.cli.commands"]` and its startable FastAPI
apps under `[project.entry-points."ristops.cli.commands.start"]` in `pyproject.toml`.
The `ristops start <app>` command discovers registered apps dynamically.

Each service's `app.py` separates `build_api()` (metadata, routes, OpenAPI configuration; no
settings, no I/O), registered under `ristops.cli.commands.openapi.export`, from `create_app()`
(telemetry, settings, authN/authZ, middleware), registered under `ristops.cli.commands.start`.

### Committed API schemas

Each service's OpenAPI schema (`packages/<package>/openapi.json`) and the bff-web GraphQL SDL
(`ristops-web/graphql/schema.gql`) are committed, so API changes show up in review. They are
generated, never edited by hand: the `export-api-schemas` pre-commit hook
(`.pre-commit-config.yaml` at the repository root) runs `scripts/export-api-schemas.sh`, which
exports every app registered under `ristops.cli.commands.openapi.export` plus the SDL. When the
hook rewrites a schema it stops the commit; review the diff, stage the files and commit again.

### Inter-service HTTP

`HttpClient` from `ristops-lib-core` wraps `httpx.AsyncClient`. It injects
`Authorization: Bearer <jwt>` from the current `AsyncContext` into outgoing requests. Trace
propagation across services is not manual: `HTTPXClientInstrumentor` (`ristops-lib-otel`) injects
the W3C `traceparent` header automatically when telemetry is enabled, so a request into any
service continues the caller's trace without any header-forwarding code.

### Redis streams

`be-authz` consumes two Redis streams (user events, resource events) using
`RedisStreamConsumer`. Producers publish via `RedisStreamProducer`. Consumer groups ensure
at-least-once delivery; stale messages are reclaimed with `XAUTOCLAIM`.

A trace normally ends at a queue boundary — the producer's request finishes long before a
consumer picks the message up. `BaseEvent` (`ristops-lib-be`) carries this across the gap: every
event published on a stream gets a `traceparent` field (W3C trace context of the span that
published it) alongside `correlation_id` (the trace ID, same source). `RedisStreamConsumer`
extracts `traceparent` from the payload and opens its processing span inside that context, so the
consumer-side span is part of the *same* trace as the producing request, not a disconnected one.
Both fields are `None`/absent with no active span (telemetry disabled).

### Database access patterns

* **PostgreSQL** (`be-authn`): SQLAlchemy async sessions via `AsyncSqlSessionProvider`. Decorate
  a route or function with `@sql_transactional` to open a session; if one is already open it is
  reused (join-if-exists). Access the session with `get_sql_session()`. Use `@with_sql_db` on
  CLI entry points to configure the provider before any transactional call.
* **Neo4j** (`be-authz`): same pattern via `@neo4j_transactional`, `get_neo4j_transaction()`,
  and `@with_neo4j_db` for CLI commands.

## Adding a new endpoint

Step-by-step conventions for scaffolding a new endpoint in a Postgres-backed domain service
(`be-venue`, `be-reservation`, `be-authn`). `be-authz` (Neo4j) differs — noted inline where it
does. Worked examples to cross-check against: `ristops-be-venue/.../domain/venue/` and
`ristops-be-reservation/.../domain/service/`.

### 1. Locate or create the subdomain module

Each domain package is organized as `src/ristops_be_<service>/domain/<subdomain>/`:

```text
entities.py   # SQLAlchemy ORM entities (Postgres). be-authz: domain/models.py Pydantic node classes instead
schema.py     # Pydantic request/response/search schemas
routers.py    # FastAPI APIRouter + route handlers
service.py    # business logic, queries, conflict checks
events.py     # optional: domain events published to a Redis stream
```

Before adding a new subdomain, check whether an existing one already covers the concept and
extend it instead of creating a new one. Enums/types shared across subdomains of the same
service go in `domain/models.py`.

### 2. Entity model

Check `entities.py` for an existing entity first. Each service declares its own declarative
`Base` in `database.py` — there is no shared base/mixin across services, so id/timestamp columns
are repeated per entity:

```python
class Base(_DeclarativeBase):
    __table_args__ = make_table_args()  # binds the service's SCHEMA_NAME
```

New entity skeleton:

```python
class ThingEntity(Base):
    __tablename__ = "things"
    __table_args__ = make_table_args(UniqueConstraint("venue_id", "name"))

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    venue_id: Mapped[UUID] = mapped_column(ForeignKey(f"{SCHEMA_NAME}.venues.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(20))  # enums stored as plain text, validated by Pydantic
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
```

**Register it** — every new entity class must be imported into `domain/__init__.py` and added to
that module's `MODELS` tuple (e.g. `ristops-be-reservation/.../domain/__init__.py`):

```python
from ristops_be_<service>.domain.<subdomain>.entities import ThingEntity

MODELS = (
    ...,
    ThingEntity,
)
```

`MODELS` is what `ristops sql-database generate-ddl`/`nuke` reads to create or drop tables —
forgetting to add a new entity here means its table is never created.

`be-authz` only: define a plain Pydantic model with a `__label__` class attribute in
`domain/models.py` instead, and persist it via raw Cypher inside a `@neo4j_transactional`
function using `get_neo4j_transaction()`.

### 3. Schemas — lib-core vs service

`ristops-lib-core` owns generic building blocks only — reuse them, don't redefine:

* `ristops_lib_core.pydantic.types` — `ObjectUUID`, `CreatedAt`, `UpdatedAt`, `DeletedAt`
* `ristops_lib_core.schema.pagination` — `PaginationParams`, `SortableQuery`, `SearchQuery`, `Page[TItem]`
* `ristops_lib_core.schema.authz` — `ResourceType`, `AuthorizationResource`, `AuthorizationGrant`

Everything domain-specific lives in the service's own `schema.py`:

```python
class ThingCreationRequest(BaseModel):
    name: str
    venue_id: ObjectUUID


class ThingResponse(BaseModel):
    id: ObjectUUID
    name: str
    created_at: CreatedAt
    updated_at: UpdatedAt


class ThingSortField(StrEnum):
    NAME = "name"


class ThingSearchFilter(BaseModel):
    name: str | None = None


class ThingSearchQuery(SearchQuery, ThingSearchFilter):
    sort_field_enum: ClassVar[type[StrEnum]] = ThingSortField
```

### 4. Router (`routers.py`)

Decoration order, top to bottom: `@router.<method>(...)` → `@policy(...)` → `@sql_transactional`
→ handler.

**Policy / authz** — every non-`@public` route needs `@policy(...)` or it 500s at request time
(deny-by-default, enforced centrally by `AuthZInterceptor`). Pair a resource resolver with
permission strings. A `BaseResourceResolver(ResourceType.X)` used by more than one handler in the
router is declared once as a module-level constant, not re-created inline per endpoint (see
`_venue_path_resolver` in `venue/routers.py`); a one-off `resolve_static_resource(...)` call tied
to a single endpoint's permission string is fine written inline:

```python
_thing_path_resolver = BaseResourceResolver(ResourceType.THING)


@router.post("/things")
@policy(Policy(_thing_path_resolver, "thing:add"))
@sql_transactional
async def create_thing(request: ThingCreationRequest) -> ThingResponse:
    thing = await create_thing_entity(request)
    return ThingResponse.model_validate(thing, from_attributes=True)
```

* `BaseResourceResolver(ResourceType.X)` reads `{x}_id` from the path. Other resolvers:
  `resolve_static_resource`, `resolve_path_attribute`, `resolve_query_attribute`,
  `resolve_body_attribute`.
* New resource type → add a member to `ResourceType` in `ristops_lib_core.schema.authz`, then
  publish a lifecycle event (`publish_resource_created_event`) so `be-authz` creates the Neo4j
  node reactively. There is no central resolver registry to update.
* Permission strings (e.g. `"thing:add"`) are free-form `scope:action` — they only need to match
  a Role grant in Neo4j, they aren't declared anywhere centrally.

**Transaction decorator** — `@sql_transactional` (Neo4j: `@neo4j_transactional`) always goes
directly on the router handler, never on a `service.py` function, as the innermost decorator. It
opens a session or joins an already-open one; service functions read it via `get_sql_session()`.

**DI for resource-access lists** (mirrors venue's `get_venues`) — for list endpoints scoped to
"what the caller can see":

```python
@router.get("/things")
@policy()
@sql_transactional
async def get_things(
    search: Annotated[ThingSearchQuery, Query()],
    grants: Annotated[
        ListUserResourceGrantsResponse,
        Depends(
            AuthorizationResourceGrantsFetcher(
                authz_client_factory,
                ResourceType.THING,
                "thing:get",
                override_policies=(Policy(resolve_static_resource("*", ResourceType.APP), "thing:list"),),
            )
        ),
    ],
) -> Page[ThingResponse]:
    scope = ThingSearchScope.from_grants(grants)
    return await search_things(search, scope)
```

If the caller holds the `override_policies` permission (e.g. an admin-level `thing:list`), the
fetcher returns `None` (unrestricted); otherwise it returns the `THING` resources the caller
individually holds `thing:get` on. Build a `BaseModel` scope from it the same way venue does
(`VenueSearchScope.from_grants`, `venue/service.py`) — a `<resource>_ids: list[str] | None` field,
`None` meaning unrestricted — and AND `id.in_(scope.<resource>_ids)` into the query's WHERE
conditions only when the scope isn't `None`.

**409 checks** always happen in `service.py`, next to the business rule — never in the router.
The router only documents the possibility: `responses={HTTPStatus.CONFLICT: {"model": ErrorResponse}}`.

**Params/body organization** — path params as `Annotated[T, Path(...)]`, query bundles as a
single `Annotated[SearchQueryClass, Query()]`, body as a bare Pydantic model parameter — all as
sibling function arguments, no wrapper object.

**List/search endpoints** always take one `SearchQuery`-derived class (pagination + sort + a
domain filter, see step 3) and return `Page[TItem]`.

**Entity → schema mapping** — single-item responses use
`ResponseModel.model_validate(entity, from_attributes=True)` inline in the router. List/search
endpoints go through `SearchQueryExecutor`/`PaginatedSearchQueryExecutor`
(`ristops_lib_sql.search`), which does the same mapping internally; override with `model_mapper=`
only if the default isn't sufficient.

### 5. `service.py`

Flat `async def` functions, no service class or DI container. Fetch the session with
`get_sql_session()` — never pass it as a parameter. Raise not-found/conflict as plain
`fastapi.HTTPException` (no custom exception hierarchy exists in this codebase) — a shared
`GenericHttpExceptionHandler` in lib-core turns any `HTTPException` into the standard
`ErrorResponse` body app-wide.

```python
async def find_thing_or_throw(thing_id: UUID) -> ThingEntity:
    session = get_sql_session()
    result = await session.scalars(select(ThingEntity).where(ThingEntity.id == thing_id).limit(1))
    thing = result.one_or_none()
    if thing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Thing not found")
    return thing


async def create_thing_entity(request: ThingCreationRequest) -> ThingEntity:
    if await _thing_name_taken(request.venue_id, request.name):
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="A thing with this name already exists")
    session = get_sql_session()
    thing = ThingEntity(**request.model_dump())
    session.add(thing)
    await session.flush()
    return thing
```

**Cross-service checks go over HTTP**, the same way the BFF talks to backends: instantiate an
`HttpClient`/`HttpClientService` for the target service (see
`ristops-be-venue/.../services/http.py` + `services/reservation.py`'s `reservation_client`,
used by `has_active_service()` to call `be-reservation`'s `GET /services` endpoint) and call it
from `service.py`. Direct same-process function calls between subdomains are only valid *within*
one package — e.g. `be-reservation`'s schedule service calling its own local `venue` subdomain
directly, because that subdomain is a local read-model of venue data synced via Redis stream, not
a real cross-service call. Treat that as the exception for local read-model subdomains, not the
general rule for talking to another microservice.

### 6. Mirroring on the BFF (`ristops-bff-web`)

The BFF is a thin mirror for fetching/mutating data through the backends — it holds no business
logic or validation of its own, and backend-to-backend orchestration inside the BFF is
discouraged. Today the only exception is login, which does orchestrate across services; don't
treat it as a pattern to repeat for a new domain.

* Add a `<domain>_client = HttpClient(...)` instance (see `ristops_bff_web/http.py`), bound to
  `RISTOPS_BE_<DOMAIN>_URL` in `app.py`'s `with_clients(...)` lifespan setup.
* `domain/<x>/service.py` in the BFF calls
  `<domain>_client.client.get/post/patch/delete(url=..., params=..., json=...)` with relative
  paths, using a `ResponseTransformer` to coerce date/datetime strings back to Python types.
* `domain/<x>/graphql.py` — define `@strawberry.type`/`@strawberry.input` classes with snake_case
  fields (Strawberry auto-exposes them as camelCase in the schema) and a `from_dict(obj)`
  classmethod mapping the REST JSON 1:1 onto the type.
* Query resolvers call the service function and wrap the result, e.g.
  `Page.from_dict(page, Thing.from_dict)`. Mutation resolvers call the service function and map
  the returned dict(s) the same way.
* Wire resolvers as `strawberry.field` / `strawberry.mutation(resolver=...)` on the domain's
  `Query`/`Mutation` type, merged into the root schema via `merge_types` in
  `ristops_bff_web/graphql/schema.py`.
* Errors need no manual translation: `HttpClient`'s `raise_for_status` hook already converts any
  non-2xx REST response into an `HTTPException`; `ErrorHandlingExtension` on the GraphQL schema
  rewrites that into a GraphQL error with `extensions.code` set to the original REST status.

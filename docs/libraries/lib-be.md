# ristops-lib-be

Backend-only helpers: authentication middleware, deny-by-default authorization interceptor,
and stream event base types.

> Source: [ristops-lib-be](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-lib-be/README.md)

## Authentication middleware

This module addresses the need to authenticate every incoming request in a single place, without
duplicating validation logic across routes. `JwtAuthNMiddleware` intercepts each request, extracts
the `Authorization: Bearer` header, validates the token, and stores `user_id` and the raw JWT in
`APP_CONTEXT`. Routes registered as `@public` are skipped entirely.

`SessionAuthNMiddleware` (used by `bff-web`) extends the same base class but reads from a
server-side Redis session instead of a header. It also handles transparent JWT refresh: if the
stored token is within 60 seconds of expiry, it is refreshed before the request proceeds.

## Authorization interceptor

`AuthZInterceptor` is a FastAPI dependency that centralises all authorization decisions.
The motivation is to avoid scattering ACL checks across individual route handlers and to make
it impossible to forget to protect a route.

It is deny-by-default: every route that is not explicitly `@public` must carry a `@policy`
decorator, or the service returns 500. This surfaces misconfigured routes immediately rather than
silently allowing access.

| Route state | Outcome |
|-------------|---------|
| `@public` | Skipped — authentication already waived |
| `@policy()` — no arguments | Any authenticated user is allowed |
| `@policy(Policy(...))` — with grants | ACL check enforced |
| No decorator | 500 — developer error |

`@policy` accepts one or more `Policy` objects. Each `Policy` holds a resource resolver and a
list of permissions. The resolver extracts the resource ID from the request (path param, query
param, or body field) at runtime, so the check is always scoped to the specific resource being
accessed.

```python
@router.get("/{location_id}")
@policy(Policy(BaseResourceResolver(ResourceType.LOCATION), "location~get"))
@neo4j_transactional
async def get_location(location_id: str): ...
```

## Stream event base types

This module provides the base class and event type enum shared by all Redis stream producers
and consumers. `BaseEvent` captures `correlation_id` from `APP_CONTEXT` automatically at
instantiation time via a Pydantic `default_factory`, so producers do not need to set it manually
and the trace context flows through the message boundary without any extra code.

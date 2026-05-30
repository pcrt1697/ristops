# Event-Driven Architecture

Services communicate asynchronously via Redis Streams. Producers publish domain events;
consumers process them independently, with at-least-once delivery guaranteed by consumer
groups and stale-message reclaim via `XAUTOCLAIM`.

## Design principles

- Stream names follow the convention `{entity}:{event-kind}`, named after the **domain
  concept** rather than the producing service. This keeps producers and consumers decoupled
  from each other — both are coupled only to the stream name.
- Event type (e.g. `created`, `deleted`) is carried in the **message payload**, not in the
  stream name. This preserves ordering guarantees within a stream: splitting event types
  across separate streams would risk processing a deletion before its creation.
- One stream per entity per event category. If a naming collision arises in the future,
  the stream name should be made more specific at that point rather than pre-emptively
  over-engineering the convention.

## Stream registry

| Stream | Producers | Consumers | Purpose |
|--------|-----------|-----------|---------|
| `user:lifecycle` | `be-authn` | `be-authz` | User created / deleted — keeps the ACL graph in sync |
| `resource:lifecycle` | any service | `be-authz` | Resource created / deleted — registers domain resources in the ACL graph |

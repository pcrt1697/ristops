# be-venue

Venue registry service. Owns the canonical list of venues and acts as the root identity
reference for all other domain services.

> Source: [ristops-be-venue](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-be-venue/README.md)

## Role in the architecture

`be-venue` is intentionally thin. It manages the lifecycle of venue records and issues the
venue IDs that `be-reservation` and the other domain services reference. Keeping it as a
standalone service means venue identity has a clear owner from the start, avoiding a
retro-fit when lifecycle operations (enable/disable, metadata) are introduced later.

Staff assignment is not a venue concern — it is handled by `be-authz` via ACL rules on
venue resources. When a venue is created, `be-venue` registers it as a `venue` resource under
`app/*` through the resource lifecycle stream, which is what lets grants be attached to it.

## Lifecycle

A venue is created `pending`, with no owner and no configuration. Its status changes only through
four actions; the plain update endpoint cannot set it. The actions are separate from the target
status because `activate` and `enable` land on different states and are allowed to different
people.

| Action | From | To | Who | Meaning |
|---|---|---|---|---|
| `activate` | `pending`, `closed` | `active` | venue owner | Open for business, or reopen after closing |
| `close` | `active` | `closed` | venue owner | Soft close: configuration and grants are kept so it can reopen |
| `disable` | `pending`, `active` | `disabled` | app admin | The owner is locked out until an admin intervenes |
| `enable` | `disabled` | `pending` | app admin | Lifts the lock; the owner must activate again |

An action from any other status is rejected with `409 Conflict`. `enable` deliberately lands on
`pending` rather than `active`, because activation has a precondition that must hold again.

**Activation requires at least one service.** A venue with nothing to book cannot open, so
`activate` asks `be-reservation` over HTTP whether the venue has a non-deleted service. This is
the one synchronous call from `be-venue` to another domain service; it reuses the existing service
listing rather than adding an "exists" endpoint, since a venue's list is small.

## Events

Creating or changing a venue publishes a `VenueLifecycleEvent` on the `venue:lifecycle` stream,
carrying the venue ID, its IANA timezone and its status. `be-reservation` consumes it to keep its
local venue read model, so it never calls `be-venue` to compute availability. See
[Event-Driven Architecture](../events.md).

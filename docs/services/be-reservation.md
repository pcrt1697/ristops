# be-reservation

Reservation service. Owns venue reservation configuration, tables, and reservations, and
computes slot availability.

> Source: [ristops-be-reservation](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-be-reservation/README.md)

## Role in the architecture

`be-reservation` is a single deployable with a single PostgreSQL database. Configuration
(services, opening rules and per-date overrides), tables, and reservations all live together so
the availability check that prevents double-booking can be a single atomic operation — the
reason these concerns are not split across services.

Configuration is layered: base opening rules define the defaults, and dated overrides express
exceptions (modified hours or closures). Bookable slots are never stored; they are computed at
query time from the rules plus existing reservations. The service references venue IDs issued by
`be-venue` and reads venue metadata (timezone, lifecycle status) replicated locally via an
event-driven read model, rather than calling `be-venue` on hot paths.

For the decisions behind this design, see the be-reservation entries in the
[ADRs](../adr.md).

## Domain model

- **`Service`** — a named offering at a venue (e.g. "Lunch", "Dinner"). Carries service-wide
  defaults: `turn_time_m` (reservation duration), `advance_notice_m` (booking cutoff),
  `slot_interval_m` (grid step between bookable start times — reservations use a **rolling
  window** model, not fixed turns), `grace_period_m` (no-show grace period). Soft-deleted
  (`deleted_at`), since a reservation may still reference a service after it's retired.
- **`ServiceOpening`** — the recurring base rule: one row per `(service, weekday)` (enforced
  unique) — deliberately **periodless**: no validity date range, so a base opening applies
  indefinitely once created rather than silently expiring if not renewed. Seasonal/temporary
  changes go through overrides instead, which are explicit and visible.
- **`ServiceOpeningOverride`** — a date-ranged exception that fully **replaces** the base hours
  for that period (not merged/added). No natural single-value key (a service can have many,
  non-overlapping override periods), so bulk edits are reconciled by `id`, not by a business key.
- **`ServiceClosing`** — a date-ranged full closure of a service. Same `id`-based reconciliation
  as overrides.
- **`ServiceOccurrence`** — a materialized, stateful record of a service actually running on a
  specific date (`(service, date)` unique), with an explicit open/close lifecycle (manager,
  owner, or server opens it; manager closes it) — the anchor for financial close-out and
  no-show handling.

Rule precedence when resolving what applies on a given date: **base opening → override
(replaces) → closing (wins)**.

Venue owners can force-book reservations that violate computed availability (e.g. phone
bookings); only the customer-facing path needs the atomic `INSERT ... WHERE booked < capacity`
guard.

## Local venue read model

be-reservation keeps a thin, read-only projection of each venue (`timezone`, lifecycle
`status`) rather than calling `be-venue` synchronously. It's kept in sync via a dedicated
`venue:lifecycle` Redis stream, autonomous to be-venue (not a shared library type — venue is a
domain service, not infrastructure, so each side owns its own narrow event schema). Writing new
service/opening/override/closing config is blocked while the owning venue's status is
`DISABLED` or `CLOSED` (via a router-level dependency, not buried in service functions);
`PENDING` is explicitly allowed, since that's the state config is authored *during*. Reads are
never blocked by venue status.

## Timekeeping conventions

- **Recurring config** (opening hours, weekday rules) — naive, no timezone, interpreted through
  the venue's IANA timezone at computation time. This is what lets a rule mean "19:00 every
  Friday" correctly across DST changes.
- **Calendar dates** (override/closing ranges, occurrence date) — plain `DATE`, venue-local, no
  time component.
- **Absolute instants** (audit timestamps, occurrence open/close) — UTC, unambiguous.

## Search/query infrastructure

Shared with the rest of the backend: `SearchQueryExecutor` (unpaginated — used here, since a
venue's service list is always small) and `PaginatedSearchQueryExecutor` (used by venue/user
search elsewhere), both in `ristops-lib-sql`, sharing the same condition-builder/sort/mapper
shape. Sorting and filtering conventions (`filter.<field>` query params, repeatable `sort` with
`-` for descending) come from `ristops-lib-core`'s `SortableQuery`/`SearchQuery` split.

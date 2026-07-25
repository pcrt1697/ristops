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
- **`CapacityOverride`** — a date-ranged, signed seat-count delta (`capacity_delta`, e.g. `+30`
  for a garden, `-10` for a partial closure) applied on top of the capacity resolved from the
  base opening or its override for that date. Independent of `ServiceOpeningOverride`: the two
  never conflict with each other and can freely overlap.
- **`ServiceClosing`** — a date-ranged full closure of a service. Same `id`-based reconciliation
  as overrides.
- **`VenueClosing`** — a date-ranged full closure of every service at a venue. Independent of
  per-service closings (a venue closing doesn't require or imply a matching `ServiceClosing`),
  but wins over them: if the venue is closed, no service at it is bookable regardless of its
  own closing/override state.
- **`ServiceOccurrence`** — a materialized, stateful record of a service actually running on a
  specific date (`(service, date)` unique), with an explicit open/close lifecycle (manager,
  owner, or server opens it; manager closes it) — the anchor for financial close-out and
  no-show handling.

Rule precedence when resolving what applies on a given date: **base opening → opening override
(replaces hours/capacity) → capacity override (adjusts the resolved capacity by a signed delta)
→ closing (wins — no availability, regardless of any override)**. A venue closing overrides
every service at that venue; a service closing overrides only that service.

`ServiceOpeningOverride`, `CapacityOverride`, `ServiceClosing`, and `VenueClosing` share the
same shape: a date range (inclusive) optionally narrowed to one `weekday` (`null` scope means
every day in the range). See "Schedule exception validation" below for how conflicting writes
across these four kinds are prevented.

Venue owners can force-book reservations that violate computed availability (e.g. phone
bookings); only the customer-facing path needs the atomic `INSERT ... WHERE booked < capacity`
guard.

## Local venue read model

be-reservation keeps a thin, read-only projection of each venue (`timezone`, lifecycle
`status`) rather than calling `be-venue` synchronously. It's kept in sync via a dedicated
`venue:lifecycle` Redis stream, autonomous to be-venue (not a shared library type — venue is a
domain service, not infrastructure, so each side owns its own narrow event schema). Writing new
service/opening/override/closing config is blocked while the owning venue's status is
`DISABLED` or `CLOSED`, enforced by a guard (`check_venue_accepts_config_changes` /
`ensure_venue_accepts_config_changes` in `domain/venue/service.py`) called at the top of every
mutating function across `domain/venue/service.py`, `domain/schedule/service.py`, and
`domain/service/service.py` — not a router-level dependency. `PENDING` is explicitly allowed,
since that's the state config is authored *during*. Reads are never blocked by venue status.

## Schedule exception validation

`ServiceOpeningOverride`, `CapacityOverride`, `ServiceClosing`, and `VenueClosing` writes are
checked for overlap before being persisted. Two rows conflict when their date ranges overlap
(inclusive) **and** their weekday scopes intersect — a `null` (every-day) scope always overlaps;
two explicit weekdays overlap only when equal.

The check is intentionally asymmetric per kind, not one shared rule:

- **Venue closing** only conflicts with other venue closings on the same venue.
- **Service closing** conflicts with other service closings on the same service **and** with
  venue closings on the service's venue (a service closing already covered by a venue-wide
  closure would be redundant) — but a venue closing does not check service closings back.
- **Opening override** and **capacity override** each only conflict with their own kind on the
  same service. They deliberately ignore closings (an override underneath a closing is fine —
  the closing wins at resolution time regardless) and ignore each other.

A conflicting create/update is rejected with `409 Conflict`. The `weekday` scope is immutable
once a row exists — an update can move dates or change the exception's own value(s), but not
re-scope the weekday; re-scoping means deleting and recreating the row. Each writable kind also
exposes a paired read-only conflict-preview query, so a caller (the frontend, in particular) can
check what a candidate period would collide with before submitting, without attempting the write
— it reuses the exact same overlap logic as the write-path check.

Because a plain check-then-insert has a race window (two concurrent writes can each see "no
conflict" and both succeed), a conflict-checked write first takes a `SELECT ... FOR UPDATE` lock
on the owning service or venue row, serializing writers against the same owner before the
overlap check runs. The service-closing path takes both locks (service, then venue), since its
check spans both tables.

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

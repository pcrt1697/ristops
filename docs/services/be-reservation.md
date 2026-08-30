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
- **`Reservation`** — a booked party at a venue: `reservation_date`, `party_size`, contact
  details, `notes`, and a `status`. Deliberately carries **no service reference**: the service is
  derived from venue + datetime whenever it is needed, so a booking survives later edits to the
  service it happens to fall under. `reservation_date` is stored as a UTC instant and presented
  as naive venue-local wall-clock, to the minute.

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

## Reservation lifecycle

A booking is created `pending` and moves on through a single status-change operation, whose
request is discriminated on `action` — the *verb* the caller performs — rather than on the
resulting status, because the required permission differs per verb and several verbs would
otherwise be indistinguishable from their target state.

| Action | Result | Permission | Meaning |
|---|---|---|---|
| — | `pending` | `reservation:add` | The status a booking is created with; not an action. |
| `confirm` | `confirmed` | `reservation:confirm` | The venue accepts it; the table is held. |
| `reject` | `rejected` | `reservation:reject` | The venue declines a booking still awaiting an answer. |
| `cancel` | `canceled` | `reservation:cancel` | The customer called it off. |
| `check_in` | `checked_in` | `reservation:check-in` | The party arrived; records `arrival_time`. |
| `no_show` | `no_show` | `reservation:no-show` | The party never arrived. |
| `withdraw` | `withdrawn` | `reservation:withdraw` | The venue gives up a booking it had already accepted. |

The three ways a booking can end without the party arriving are distinguished by *who* ended it
and *when*: `rejected` is the venue declining before accepting, `canceled` is the customer's own
doing, and `withdrawn` is the venue giving up a booking it had accepted — typically after a
closure or schedule change made it impossible to honor.

`check_in` records `arrival_time` from the request, defaulting to the current venue-local time.
Any action may carry `notes`, which **replace** the reservation's existing notes rather than
appending to them.

**There is no from-state validation yet.** An action sets its target status directly, so nothing
currently stops a `checked_in` booking being confirmed again; the state machine is a later task.
The frontend applies its own reading of the lifecycle in the meantime, offering actions only from
`pending` and `confirmed`.

Only `pending`, `confirmed` and `checked_in` hold a seat, so only those count against capacity
when availability is computed — a rejected or canceled booking frees its seats immediately.

### Schedule violations

Editing a schedule never rewrites the bookings underneath it: shrinking hours or closing a date
leaves existing reservations untouched. Instead each booking is checked against the *current*
schedule when read, and flagged with a `violation`:

| Violation | Meaning |
|---|---|
| `no_service` | No service is open at that time any more. |
| `closed` | A venue or service closing now covers the date. |
| `outside_hours` | The turn no longer fits inside the (shrunk) opening hours. |

Only future bookings in a live status (`pending`, `confirmed`) can be violated — a `checked_in`
booking already happened, and the terminal statuses are resolved. Resolving a violation is a
human decision, which is what `withdraw` exists for; the reservation search takes a
violations-only filter that gives staff the list to work through.

Capacity overflow is deliberately *not* a violation: it belongs to a slot rather than to any one
booking, so it surfaces separately as its own over-capacity view.

## Availability reads

Two read-only views expose what the booking rules would decide, without attempting a write. Both
are previews in the same sense as the schedule conflict queries: no lock is taken, and the
definitive check still runs on the create path, under a `SELECT ... FOR UPDATE` on the resolved
service.

- **A calendar summary** over a date window — per business date, the services open that date with
  their window, effective capacity, peak concurrent booked seats and whether they are over
  capacity. This is what a month grid renders; a date with nothing open and no closing is simply
  absent. The window is capped at 62 days, so one request can never scan an unbounded stretch of
  reservations.
- **An availability preview** for a single date and party size — per open service, the slot grid
  with the seats already taken at each start time and whether the requested party fits. Slots at
  or before `now + advance_notice_m` are omitted, so a past date returns its services with empty
  slot lists: **history stays readable while booking remains now-onward**. An edited booking can
  be excluded from the seat count, so its own seats are not counted against itself.

Both build on the same helpers as the write path rather than restating the rules:
`resolve_day_slots` resolves which services open on a date (base opening → override → closing,
plus capacity deltas), and `slot_times` produces the grid — every `slot_interval_m` from the
opening, for as long as a whole `turn_time_m` still fits before closing. `_ensure_slot_available`
validates against that same `slot_times` output, so a preview and a create cannot disagree about
which start times are legal.

Seat counting is shared too: `_bookings_by_slot` buckets live bookings onto the slot each one
currently resolves to, and `_peak_concurrent_seats` sweeps their `[start, start + turn)` windows.
The over-capacity view and the calendar summary read the same numbers, which is why an
overbooked day surfaces identically in both.

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

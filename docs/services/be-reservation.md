# be-reservation

Reservation service. Owns venue reservation configuration (services, their weekly openings and
closings) and the bookings made against them, and computes per-day availability.

> Source: [ristops-be-reservation](https://github.com/pcrt1697/ristops/blob/main/ristops-backend/packages/ristops-be-reservation/README.md)

## Role in the architecture

`be-reservation` is a single deployable with a single PostgreSQL database. Configuration
(services, their openings and closings) and reservations live together so the availability check
that prevents double-booking can be a single atomic operation — the reason these concerns are not
split across services.

The model is deliberately flat: a service says when it runs and how many seats it has, a closing
takes dates away from it, and there is nothing else. Anything that would once have been an
exception — a special evening, seasonal hours, a one-off with a different capacity — is expressed
as *another service*, bounded to the dates it applies to. Bookable capacity is never stored; it
is computed at query time from the services plus existing reservations. The service references
venue IDs issued by `be-venue` and reads venue metadata (timezone, lifecycle status) replicated
locally via an event-driven read model, rather than calling `be-venue` on hot paths.

For the decisions behind this design, see the be-reservation entries in the
[ADRs](../adr.md).

## Domain model

- **`Service`** — a named offering at a venue (e.g. "Lunch", "Dinner"), valid over a date range
  and taking a fixed number of seats. `date_from` is required; `date_to` is optional and, left
  null, runs the service indefinitely. Setting both to the same date makes a **one-off service** —
  the way a special evening is modelled. `capacity` is the seats bookable on any date it runs.
  Soft-deleted (`deleted_at`), since a reservation keeps referencing its service after it is
  retired.
- **`Opening`** — the hours a service runs on one weekday: one row per `(service, weekday)`
  (enforced unique), holding `start_time` and `end_time`. An `end_time` at or before the
  `start_time` runs the opening **overnight**, closing on the following calendar day. A service
  runs on a date when its validity covers that date *and* it has an opening for that weekday.
- **`Closing`** — a date range over which the linked services do not run, venue-scoped and joined
  to one or more services through `closing_services`. A venue-wide shutdown is a closing linked to
  every service. A closing is also what makes room for a one-off service: close the regular
  service for the date, and the special one no longer overlaps it.
- **`Reservation`** — a booked party: `service_id`, `reservation_date`, `party_size`, contact
  details, `notes`, and a `status`. The booking **names its service** rather than having it
  inferred from the time, which is what lets capacity be counted per service and a closing be
  traced to the bookings it affects. `reservation_date` is stored as a UTC instant and presented
  as naive venue-local wall-clock, to the minute.

There is no slot grid and no turn duration: a booking may sit at any minute inside its service's
window, and occupancy is the sum of party sizes on a business date, checked against the service's
capacity.

### Business dates

An overnight opening makes the calendar date and the *business* date diverge: a service opening
19:00 Friday and closing 01:00 Saturday holds a 00:30 booking that belongs to Friday's service.
Resolution matches an instant against its own date's opening first and then the previous date's,
which only reaches it when that opening runs overnight. The opening's date is the business date
whose closings and capacity apply.

The reservation search's `date_from` and `date_to` are business dates too, the same as the
calendar's. A booking's business date comes from its own service, so each of the venue's
services gets its own instant range and the ranges are OR-ed together. A service's range for a
date is the calendar day, shifted past the previous night's overnight tail and stretched to that
date's own close when it runs past midnight. Consecutive days therefore never overlap and leave
no gap, and the range spans the whole day rather than the opening window, which keeps bookings
the hours no longer cover in view.

## Local venue read model

be-reservation keeps a thin, read-only projection of each venue (`timezone`, lifecycle `status`)
rather than calling `be-venue` synchronously. It is kept in sync via a dedicated
`venue:lifecycle` Redis stream, autonomous to be-venue (not a shared library type — venue is a
domain service, not infrastructure, so each side owns its own narrow event schema). Writing new
service/opening/closing config is blocked while the owning venue's status is `DISABLED` or
`CLOSED`, enforced by a guard (`check_venue_accepts_config_changes` /
`ensure_venue_accepts_config_changes` in `domain/venue/service.py`) called at the top of every
mutating function of the service subdomain — not a router-level dependency.
`PENDING` is explicitly allowed, since that is the state config is authored *during*. Reads are
never blocked by venue status.

## Service overlap validation

No two services of a venue may be open at the same instant. A booking names its service, so an
overlap is not ambiguous the way it used to be — but staff being offered two services at the same
hour is a configuration mistake, and the rule keeps a venue's schedule readable.

> Services A and B conflict iff there exists a date `D` where both validity ranges cover `D`,
> both have an opening on `weekday(D)`, no closing of either covers `D`, and their time windows
> overlap.

Windows are half-open, so a 15:00 close and a 15:00 open do not conflict. The closing clause is
what makes one-off services work: a special evening that would sit on top of the regular dinner
is accepted once the regular service is closed for that date.

The check runs in two stages. Because a window spans at most two calendar days, a candidate
opening on weekday `W` can only meet a sibling opening on `W-1`, `W` or `W+1`, and whether two
such openings overlap depends on the times and that day offset alone — so the times are compared
once against a reference week, and only the pairs that do overlap go looking for a concrete date
where both services are actually running. Searching that date is bounded when both validity
periods are: when they are not, the answer is always yes, because closings are finite date ranges
and can never remove every occurrence of a weekly opening.

Every write that can create an overlap re-runs the check and is rejected with `409 Conflict`,
naming the conflicting service and the date: a service's validity or openings changing, and a
closing being **shrunk or deleted** — which can re-expose an overlap it was hiding. Creating a
closing never can, since it only removes openings from the calendar.

Because a plain check-then-write has a race window, these writes first take a
`SELECT ... FOR UPDATE` lock on the venue row, serializing writers across the venue's services
before the check runs.

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

Only `pending`, `confirmed` and `checked_in` hold a seat, so only those count against capacity — a
rejected or canceled booking frees its seats immediately.

### Schedule violations

Editing a schedule never rewrites the bookings underneath it: shrinking hours, closing a date or
retiring a service leaves existing reservations untouched. Instead each booking is checked against
its service's *current* schedule when read, and flagged with a `violation`:

| Violation | Meaning |
|---|---|
| `no_service` | The service was deleted, or no longer runs that date. |
| `closed` | A closing now covers the date. |
| `outside_hours` | The service still runs that day, but no longer opens at that time. |

Only future bookings in a live status (`pending`, `confirmed`) can be violated — a `checked_in`
booking already happened, and the terminal statuses are resolved. Resolving a violation is a human
decision: `withdraw` gives the booking up, or editing it with a new `service_id` moves it onto a
service that can take it, checked like a new booking. The reservation search takes a
violations-only filter that gives staff the list to work through.

A booking on a service that is deleted, or closed on that date, can no longer be confirmed,
rejected, checked in or marked as a no-show, since nothing will be served; the frontend offers
only cancel and withdraw for it.

Capacity overflow is deliberately *not* a violation: it belongs to a service-date rather than to
any one booking, so it surfaces on the calendar instead.

## Availability reads

One read-only view exposes what the booking rules would decide, without attempting a write: a
**calendar summary** over a date window. Per business date it reports the services running that
date with their window, capacity, seats booked and left, booking count, and whether they are over
capacity; a date where a closing removes every service that would otherwise run is marked
`closed`. A service a closing removes that day is not in that list, since it no longer runs, so
the ones that still hold bookings needing attention (future, `pending` or `confirmed`) are
reported separately as `closed_services`, each with its booking count. Deleted services are
reported the same way, as `deleted_services`, and only when they hold such bookings. This is
what a month grid renders, and also what the booking form reads to offer a service and show its
remaining seats — a date with nothing running and no closing is simply absent. The window is
capped at 62 days, so one request can never scan an unbounded stretch of reservations.

It is a preview in the same sense as the old conflict queries: no lock is taken, and the
definitive check still runs on the create path, under a `SELECT ... FOR UPDATE` on the service
being booked. That write path is the only place the rules are enforced — the service runs the
date, no closing covers it, the instant falls inside `[opens_at, closes_at)`, and the seats
already booked into the same window leave room for the party.

Seat counting uses the window itself as the bucket: a service holds exactly one window per
business date, so any live booking whose instant falls in it belongs to that date. Bookings left
outside by a later hours change are not counted — they are violations, reported per-reservation,
not capacity.

## Timekeeping conventions

- **Recurring config** (opening hours, weekday rules) — naive, no timezone, interpreted through
  the venue's IANA timezone at computation time. This is what lets a rule mean "19:00 every
  Friday" correctly across DST changes.
- **Calendar dates** (service validity, closing ranges) — plain `DATE`, venue-local, no time
  component.
- **Absolute instants** (reservation datetimes, audit timestamps) — UTC, unambiguous.

## Search/query infrastructure

Shared with the rest of the backend: `SearchQueryExecutor` (unpaginated — used for a venue's
service list, which is always small) and `PaginatedSearchQueryExecutor` (used for closings and
reservations), both in `ristops-lib-sql`, sharing the same condition-builder/sort/mapper shape.
Sorting and filtering conventions (`filter.<field>` query params, repeatable `sort` with `-` for
descending) come from `ristops-lib-core`'s `SortableQuery`/`SearchQuery` split.

# ristops-batch-demo

Demo package for batch processing commands. Not production code — exists to illustrate how batch
jobs integrate with the CLI and the rest of the platform.

## `demo seed`

Populates a running stack with Game-of-Thrones-themed demo data by calling the real backend REST
APIs (authn, venue, reservation, authz): it registers users, creates venues, adds services to each
venue, grants venue roles, activates the venues, and books demo reservations.

```bash
ristops demo seed \
  --users packages/ristops-batch-demo/demo-data/users.json \
  --venues packages/ristops-batch-demo/demo-data/venues.json \
  --services packages/ristops-batch-demo/demo-data/services.json \
  --reservations packages/ristops-batch-demo/demo-data/reservations.json \
  --assignments packages/ristops-batch-demo/demo-data/assignments.json \
  --admin-password <admin_pwd>
```

Options:

| Option                | Env var             | Description                                   |
|-----------------------|---------------------|-----------------------------------------------|
| `-u/--users`          |                     | Path to the users JSON file (required).       |
| `-v/--venues`         |                     | Path to the venues JSON file (required).      |
| `-s/--services`       |                     | Path to the services JSON file (required).    |
| `-r/--reservations`   |                     | Path to the reservations JSON file (required).|
| `-a/--assignments`    |                     | Path to the assignments JSON file (required). |
| `-e/--admin-email`    |                     | Admin email (default `admin@ristops.com`).    |
| `-p/--admin-password` | `RISTOPS_ADMIN_PWD` | Admin password (required).                    |

Service base URLs are read from `BackendServiceSettings` (`RISTOPS_BE_AUTHN_URL`,
`RISTOPS_BE_VENUE_URL`, `RISTOPS_BE_RESERVATION_URL`, `RISTOPS_BE_AUTHZ_URL`) and must include the
`/api` prefix.

Venues are created in `PENDING` and only activated after their services exist — a venue cannot be
activated without at least one service. A venue with no entry in `services.json` is left `PENDING`.

### Config files (split by domain)

`users.json` (authn) — `password` falls back to `username` when omitted:

```json
{ "users": [ { "username": "the_headless", "email": "...", "display_name": "Eddard Stark" } ] }
```

`venues.json` (venue) — `key` is a symbolic reference used by services and assignments. Optional
`closings` take a date range away from the services they name; an empty (or omitted) `services`
list closes **every** service of the venue. Dates are a fixed annual
`dates.month_day_start/end` (`"MM-DD"`) range, materialized once per entry in
`dates.year_offsets` (relative to the current *year* only — `[-1, 0, 1]` for
previous/current/next year). The day/month are always fixed, so seed data never depends on which
day it happens to be seeded on.

```json
{ "venues": [ { "key": "stark", "name": "House Stark", "address": "...", "description": "...",
  "closings": [
    { "dates": { "month_day_start": "01-15", "month_day_end": "02-05", "year_offsets": [-1, 0, 1] },
      "services": [], "description": "Deep winter — Winterfell rests" },
    { "dates": { "month_day_start": "09-21", "month_day_end": "09-23", "year_offsets": [0, 1] },
      "services": ["A Feast in the Great Hall"], "description": "Makes room for Harvest feast" } ] } ] }
```

A closing can carry `"after_reservations": true`. A date cannot be booked once it is closed, so
this creates the closing after the demo bookings, leaving the ones it covers on a closed service
for staff to resolve. It is created before services marked `deleted` go, since a closing needs
live services.

`services.json` (reservation) — adds a service to a venue, referenced by `key`. `capacity` is the
seats bookable on any date it runs; `openings` are its weekly hours, with unique lowercase
weekdays and `HH:MM` times. An `end_time` at or before the `start_time` runs the opening
**overnight**, closing the following day.

```json
{ "services": [ { "venue": "stark", "name": "The Northern Table", "description": "...",
  "capacity": 45,
  "openings": [ { "weekday": "monday", "start_time": "12:00", "end_time": "15:00" } ] } ] }
```

Omitting `dates` runs the service indefinitely (from a year back). Giving it the same fixed annual
shape as a closing bounds the service to those dates — which is how a **one-off service** is
seeded. A special evening is a one-off service plus a closing that takes the regular service off
the same dates, since two services of a venue may not be open at once:

```json
{ "venue": "stark", "name": "Harvest feast",
  "description": "Harvest feast — replaces A Feast in the Great Hall on these dates.",
  "capacity": 80,
  "dates": { "month_day_start": "09-21", "month_day_end": "09-23", "year_offsets": [0, 1] },
  "openings": [ { "weekday": "monday", "start_time": "18:00", "end_time": "23:30" } ] }
```

A service can also carry `"deleted": true`. The seeder deletes it only after the demo bookings
are made, since a deleted service takes no new bookings, which leaves those bookings on a deleted
service for staff to resolve.

A one-off service normally lists all seven weekdays, so it runs whichever weekday its dates
happen to fall on that year. The seeder creates the indefinite services first, then the closings,
then the bounded ones — a closing has to exist before the service it makes room for.

`reservations.json` (reservation) — books a party into a venue's service, named by `service`.
Dates use the same fixed annual shape, but a booking is a **single day**, so `month_day_start`
and `month_day_end` are equal. `time` is booked as given: there is no slot grid, so any minute
inside the service's window is valid.  Optional `status` applies a follow-up action
(`confirmed` / `rejected` / `canceled`); omit it to leave the booking pending.

```json
{ "reservations": [ { "venue": "stark", "service": "A Feast in the Great Hall",
  "dates": { "month_day_start": "09-04", "month_day_end": "09-04", "year_offsets": [0, 1] },
  "time": "19:00", "party_size": 12, "contact_name": "Eddard Stark",
  "contact_phone_number": "...", "contact_email": "...", "notes": "...",
  "status": "confirmed" } ] }
```

A booking after midnight on an overnight service is dated the following calendar day, since
that is when it happens: `00:30` on the 15th belongs to the evening service of the 14th, and is
listed and counted under the 14th.

Bookings are **future-only**: a booking cannot be created in the past, so an occurrence that
materializes on an elapsed date is skipped. Those — along with occurrences the backend refuses
(a closed date, a time outside the window, a full service, or a weekday the service does not
open, since a fixed `MM-DD` lands on a different weekday each year) — are skipped and counted in
the completion log rather than failing the run. `year_offsets` is therefore `[0, 1]` rather than
the closings' `[-1, 0, 1]`: a previous-year booking would always be skipped. Check-in and no-show
are deliberately not offered as a `status`, since a future booking cannot already have arrived.

`assignments.json` (authz) — grants a role to users on a venue, referenced by key/username:

```json
{ "assignments": [ { "venue": "stark", "role_id": "venue.owner", "usernames": ["the_headless"] } ] }
```

Usernames double as passwords, so every username must be at least 8 characters.

### Prerequisites

The stack must be running and already seeded with the admin user and roles:

```bash
ristops seed-authn -p <admin_pwd>   # admin user (authn)
ristops seed-authz                  # roles + admin ACL (authz)
```

Because there is no user-lookup-by-username API, the seed maps usernames to ids from the creation
responses in-memory and is **not** idempotent. Re-run against a freshly reset dataset.

The whole nuke → seed-services → seed-demo flow is scripted (defaults match the local dev setup, and
requires the backend services to be running):

```bash
./scripts/reset-demo.sh
```

Equivalent manual steps:

```bash
ristops sql-database nuke be-authn -f
ristops sql-database nuke be-venue -f
ristops sql-database nuke be-reservation -f
ristops nuke-authz -f
ristops seed-authn -p <admin_pwd>
ristops seed-authz
ristops demo seed --users ... --venues ... --services ... --reservations ... --assignments ... --admin-password <admin_pwd>
```

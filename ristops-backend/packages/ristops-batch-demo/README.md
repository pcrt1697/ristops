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
`closings` are **venue-wide** (close every service for a date range, same `dates` / optional
`weekday` shape as service closings), seeded via be-reservation's `/venues/{id}/closings`:

```json
{ "venues": [ { "key": "stark", "name": "House Stark", "address": "...", "description": "...",
  "closings": [ { "dates": { "month_day_start": "01-15", "month_day_end": "02-05",
    "year_offsets": [-1, 0, 1] }, "description": "Deep winter — Winterfell rests" } ] } ] }
```

`services.json` (reservation) — adds a service to a venue, referenced by `key`; all duration fields
are in minutes. Optional `openings` set the service's weekly hours (open days); weekdays must be
unique and lowercase, times are `HH:MM`:

```json
{ "services": [ { "venue": "stark", "name": "The Northern Table", "description": "...",
  "turn_time_m": 60, "advance_notice_m": 120, "slot_interval_m": 15, "grace_period_m": 15,
  "openings": [ { "weekday": "monday", "capacity": 40, "start_time": "12:00", "end_time": "15:00" } ] } ] }
```

Optional `overrides` (special hours/capacity for a date range) and `closings` (service closed) add
calendar exceptions. Their dates are a fixed annual `dates.month_day_start/end` (`"MM-DD"`) range,
materialized once per entry in `dates.year_offsets` (relative to the current *year* only —
`[-1, 0, 1]` for previous/current/next year). The day/month are always fixed, so seed data never
depends on which day it happens to be seeded on.

Both accept an optional lowercase `weekday` that scopes the exception to a single weekday within
the range (null/omitted = every day) — e.g. "closed every Monday all summer":

```json
"overrides": [
  { "dates": { "month_day_start": "09-21", "month_day_end": "09-23", "year_offsets": [-1, 0, 1] },
    "capacity": 80, "start_time": "18:00", "end_time": "23:30", "description": "Harvest feast" },
  { "dates": { "month_day_start": "06-01", "month_day_end": "08-31", "year_offsets": [-1, 0, 1] },
    "weekday": "friday", "capacity": 65, "start_time": "18:00", "end_time": "23:59",
    "description": "Extended service every Friday (summer)" }
],
"closings": [
  { "dates": { "month_day_start": "10-10", "month_day_end": "10-11", "year_offsets": [-1, 0, 1] },
    "description": "Kingsmoot recess" },
  { "dates": { "month_day_start": "06-01", "month_day_end": "07-31", "year_offsets": [-1, 0, 1] },
    "weekday": "monday", "description": "Closed every Monday (early summer rest)" }
]
```

Optional `capacity_overrides` add a signed seat delta on top of the resolved capacity for a date
range (same `dates` / optional `weekday` shape) — e.g. a summer garden that adds seats:

```json
"capacity_overrides": [
  { "dates": { "month_day_start": "06-01", "month_day_end": "08-31", "year_offsets": [-1, 0, 1] },
    "capacity_delta": 30, "description": "Godswood garden (summer)" }
]
```

`reservations.json` (reservation) — books a party at a venue's service. Dates use the same fixed
annual `dates` shape as the schedule exceptions, but a booking is a **single day**, so
`month_day_start` and `month_day_end` are equal. `time` is a *preference*: the seeder asks
`/reservations/availabilities` what is open that day and books the bookable slot nearest it, so the
slot grid is never reimplemented here. Optional `status` applies a follow-up action
(`confirmed` / `rejected` / `canceled`); omit it to leave the booking pending.

```json
{ "reservations": [ { "venue": "stark", "service": "A Feast in the Great Hall",
  "dates": { "month_day_start": "09-04", "month_day_end": "09-04", "year_offsets": [0, 1] },
  "time": "19:00", "party_size": 12, "contact_name": "Eddard Stark",
  "contact_phone_number": "...", "contact_email": "...", "notes": "...",
  "status": "confirmed" } ] }
```

Bookings are **future-only**: `POST /reservations` enforces the service's advance notice, so an
occurrence that materializes on an elapsed date cannot be created. Those — along with occurrences
falling on a closed day, or on a weekday the service does not open (a fixed `MM-DD` lands on a
different weekday each year) — are skipped and counted in the completion log rather than failing
the run. `year_offsets` is therefore `[0, 1]` rather than the schedule exceptions' `[-1, 0, 1]`:
a previous-year booking would always be skipped. Check-in and no-show are deliberately not
offered as a `status`, since a future booking cannot already have arrived.

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

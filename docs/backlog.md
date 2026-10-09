# Backlog

Open work that is known but not scheduled.

## Reservations (`be-reservation`)

1. **Optimize the date filter of the reservation search**. `_date_condition` loads the venue services and
   their schedules on every dated search, although `list_reservations` has already loaded a `VenueScheduleSnapshot` with
   the same data. Reuse the snapshot and load schedules only for deleted services, and only when they exist.
   `list_calendar_days` repeats the same work in `_deleted_services_by_date`; one shared loader would serve both.
   `_booked_seats` also sums `party_size` in Python after loading whole rows; use a SQL `SUM`.
2. **History of closed and deleted services**. Closed or deleted services only list bookings that need attention
   (future pending or confirmed). Past or checked-in bookings of a deleted service are unreachable from the day view.
   Decide whether history should be reachable.
3. **Orphan tables on `ristops sql-database nuke`**. It only drops tables listed in `MODELS`, so a removed model leaves
   its table behind. Proposed fix: drop the schema with `CASCADE`. It touches the shared `ristops-lib-sql`, so it needs
   a decision first.
4. **Automated tests**. None exist. The ad-hoc scripts used to check the overlap rule, slot resolution,
   business-day bounds and demo data were discarded; they are worth turning into real tests.
5. **UI walk-through of the reservation page**. The booking form, closings modal, weekly-hours overlap toast and the
   calendar dot with its hover card were only type-checked and built when they were written.
6. **From-state validation for status actions**. An action sets its target status directly, whatever the current status.
7. **Clearing a field through the BFF**. The update payload sends only provided fields, so a `null`
   cannot clear a value.

## Access control (`be-authz`, admin panel)

1. **Role list disclosure**. `GET /roles` is open to any authenticated user and exposes the permission model.
   Accepted as low severity. Preferred refinement: return `permissions` only to callers holding a management permission, keeping
   id, name and description for assignment UIs. Stricter fallback: gate the whole query behind `role~list`.

## Frontend workspace

Phase 1 of the app shell (header, venue control, venue drawer, current venue) is done. Remaining:

1. Venue inner section with its sidebar items and a dashboard.
2. Resume on login, or auto-select the venue when the user has exactly one.
3. Unsaved-form guard when leaving a page, as a shared modal or route guard.
4. Server-side user preferences, as a JSONB column in `be-authn` (not in authz).

## Planned features

- Menu management
- Staff shift scheduling
- Order workflow

## AI assistant

Design under discussion, see [AI assistant design](design/ai-assistant.md). No implementation started.

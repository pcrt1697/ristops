import asyncio
import logging
from datetime import date, datetime, time
from http import HTTPStatus
from typing import Awaitable, Callable

from fastapi import HTTPException

from ristops_batch_demo.seed.models import (
    DemoAssignments, DemoDateRange, DemoReservation, DemoReservations, DemoService,
    DemoServices, DemoUsers, DemoVenues,
)
from ristops_batch_demo.services.http import (
    authn_client, authz_client, reservation_client, venue_client,
)
from ristops_lib_core.context import APP_CONTEXT, ContextKey

_logger = logging.getLogger(__name__)


def _expand_dates(anchor: DemoDateRange) -> list[tuple[date, date]]:
    """Materialize a fixed annual 'MM-DD' date spec into concrete `(start, end)` ranges, one per
    entry in `year_offsets` (relative to the current year only — never to today's exact date, so
    seed data is stable regardless of when it is seeded)."""
    current_year = date.today().year
    start_month, start_day = (int(part) for part in anchor.month_day_start.split("-"))
    end_month, end_day = (int(part) for part in anchor.month_day_end.split("-"))
    return [
        (
            date(current_year + offset, start_month, start_day),
            date(current_year + offset, end_month, end_day),
        )
        for offset in anchor.year_offsets
    ]

# Follow-up action that moves a seeded booking to the demo status asked for. Only the
# actions valid on a future booking are offered: it cannot already have arrived.
_RESERVATION_STATUS_ACTIONS: dict[str, str] = {
    "confirmed": "confirm",
    "rejected": "reject",
    "canceled": "cancel",
}

# Retry budget for ACL grants: venue/user creation propagates to authz asynchronously
# over Redis, so the resource/user node may not exist yet and the grant returns 404.
_GRANT_MAX_ATTEMPTS = 6
_GRANT_BACKOFF_BASE_S = 0.5


class DemoSeeder:
    """Seed demo users, venues, and role assignments through the backend REST APIs."""

    def __init__(
            self,
            users: DemoUsers,
            venues: DemoVenues,
            services: DemoServices,
            reservations: DemoReservations,
            assignments: DemoAssignments,
            admin_email: str,
            admin_password: str,
    ) -> None:
        self._users = users
        self._venues = venues
        self._services = services
        self._reservations = reservations
        self._assignments = assignments
        self._admin_email = admin_email
        self._admin_password = admin_password
        self._user_ids: dict[str, str] = {}
        self._venue_ids: dict[str, str] = {}
        # Venue ids that received at least one service, and so may be activated.
        self._venues_with_services: set[str] = set()
        # Service periods by (venue key, service name), so closings and bookings can name a
        # service rather than carry an id. A service repeated over several years has one entry
        # per period, and a booking resolves to the one covering its date.
        self._service_ids: dict[tuple[str, str], list[tuple[date, date | None, str]]] = {}
        self._service_count = 0
        self._services_to_delete: list[tuple[str, str]] = []
        self._deleted_count = 0
        self._closing_count = 0
        self._reservation_count = 0
        self._reservation_skipped = 0

    async def run(self) -> None:
        """Log in as admin, create users, venues, services and bookings, grant roles, and
        activate."""
        await self._login_as_admin()
        await self._create_users()
        await self._create_venues()
        # Order matters. The closings that name a service come before the bounded services,
        # because a closing is what frees a date for a one-off that would otherwise overlap a
        # regular service. The venue-wide ones come last, so they cover those one-offs too.
        await self._create_services(bounded=False)
        await self._create_closings(venue_wide=False, after_reservations=False)
        await self._create_services(bounded=True)
        await self._create_closings(venue_wide=True, after_reservations=False)
        await self._grant_roles()
        await self._activate_venues()
        # Bookings come last: a venue only accepts them once it is ACTIVE.
        await self._create_reservations()
        # Closings meant to cover those bookings can only be made once the bookings exist, and
        # before the services marked as deleted go, since a closing needs live services.
        await self._create_closings(venue_wide=False, after_reservations=True)
        await self._create_closings(venue_wide=True, after_reservations=True)
        await self._delete_services()
        _logger.info(
            "Demo seed complete: %d users, %d venues, %d services (%d deleted), %d closings, "
            "%d reservations (%d skipped).",
            len(self._user_ids),
            len(self._venue_ids),
            self._service_count,
            self._deleted_count,
            self._closing_count,
            self._reservation_count,
            self._reservation_skipped,
        )

    async def _login_as_admin(self) -> None:
        """Authenticate as admin and store the access token in the async context."""
        response = await authn_client.client.post(
            "/auth/login",
            json={"email": self._admin_email, "password": self._admin_password},
        )
        access_token = response.json()["access_token"]
        # inject_auth_header reads this key to attach the Bearer token to every call.
        APP_CONTEXT.set(ContextKey.JWT, access_token)
        _logger.info("Authenticated as admin [%s].", self._admin_email)

    async def _create_users(self) -> None:
        """Register every demo user (public endpoint) and record their ids."""
        for user in self._users.users:
            response = await authn_client.client.post(
                "/users",
                json={
                    "username": user.username,
                    "display_name": user.display_name,
                    "email": user.email,
                    "password": user.login_password,
                },
            )
            user_id = response.json()["id"]
            self._user_ids[user.username] = user_id
            _logger.info("Created user [%s] -> %s", user.username, user_id)

    async def _create_venues(self) -> None:
        """Create every demo venue and record their ids by symbolic key."""
        for venue in self._venues.venues:
            response = await venue_client.client.post(
                "/venues",
                json={
                    "name": venue.name,
                    "address": venue.address,
                    "description": venue.description,
                    "timezone": venue.timezone,
                },
            )
            venue_id = response.json()["id"]
            self._venue_ids[venue.key] = venue_id
            _logger.info("Created venue [%s] -> %s", venue.key, venue_id)

    async def _create_services(self, bounded: bool) -> None:
        """Create the demo services under their venues, resolving the venue by symbolic key.

        Runs twice: once for the services with no date range (they run indefinitely), and once,
        after the closings exist, for the bounded ones — a one-off service usually overlaps a
        regular service's hours, and it is the closing on that date that makes room for it.
        """
        for service in self._services.services:
            if (service.dates is not None) != bounded:
                continue
            venue_id = self._venue_ids.get(service.venue)
            if venue_id is None:
                _logger.warning(
                    "Skipping service [%s] for unknown venue key [%s].",
                    service.name,
                    service.venue,
                )
                continue
            for date_from, date_to in self._service_periods(service):
                await self._create_service_on(venue_id, service, date_from, date_to)

    @staticmethod
    def _service_periods(service: DemoService) -> list[tuple[date, date | None]]:
        """The validity periods to create a service for: one per expanded date range, or a single
        open-ended period starting a year back when the service carries no dates."""
        if service.dates is None:
            return [(date(date.today().year - 1, 1, 1), None)]
        return [
            (date_from, date_to) for date_from, date_to in _expand_dates(service.dates)
        ]

    async def _create_service_on(
            self,
            venue_id: str,
            service: DemoService,
            date_from: date,
            date_to: date | None,
    ) -> None:
        """Create one validity period of a demo service, then set its weekly openings."""
        response = await reservation_client.client.post(
            "/services",
            json={
                "venue_id": venue_id,
                "name": service.name,
                "description": service.description,
                "date_from": date_from.isoformat(),
                "date_to": date_to.isoformat() if date_to is not None else None,
                "capacity": service.capacity,
            },
        )
        service_id = response.json()["id"]
        self._venues_with_services.add(venue_id)
        self._service_count += 1
        if service.deleted:
            self._services_to_delete.append((service_id, service.name))
        self._service_ids.setdefault((service.venue, service.name), []).append(
            (date_from, date_to, service_id)
        )
        _logger.info(
            "Created service [%s] on venue [%s] from %s -> %s",
            service.name,
            service.venue,
            date_from,
            service_id,
        )
        await self._upsert_openings(service_id, service)

    async def _write_with_authz_retry(
            self,
            do_request: Callable[[], Awaitable[object]],
            label: str,
    ) -> None:
        """Run a write authorized against a just-created resource, retrying on 403/404 to
        absorb authz propagation lag.

        A newly created resource's authz node and its link to the parent propagate
        asynchronously over Redis. Until that lands the ReBAC check finds no granting path and
        denies (403), so we retry with backoff — mirroring ``_grant_with_retry``'s tolerance
        for the same lag. This affects `schedule:*` writes (authorized against the SERVICE
        just created) and reservation actions (authorized against the RESERVATION just
        created) alike.
        """
        for attempt in range(1, _GRANT_MAX_ATTEMPTS + 1):
            try:
                await do_request()
                return
            except HTTPException as exc:
                not_ready = exc.status_code in (HTTPStatus.FORBIDDEN, HTTPStatus.NOT_FOUND)
                if not not_ready or attempt == _GRANT_MAX_ATTEMPTS:
                    raise
                delay = _GRANT_BACKOFF_BASE_S * 2 ** (attempt - 1)
                _logger.info(
                    "%s authz not ready (attempt %d/%d), retrying in %.1fs...",
                    label,
                    attempt,
                    _GRANT_MAX_ATTEMPTS,
                    delay,
                )
                await asyncio.sleep(delay)

    async def _upsert_openings(self, service_id: str, service: DemoService) -> None:
        """Replace the weekly openings for a just-created service, if any are defined."""
        if not service.openings:
            return
        body = {"openings": [opening.model_dump() for opening in service.openings]}
        await self._write_with_authz_retry(
            lambda: reservation_client.client.put(f"/services/{service_id}/openings", json=body),
            f"openings for [{service.name}]",
        )
        _logger.info(
            "Set %d weekly openings on service [%s].", len(service.openings), service.name
        )

    async def _create_closings(self, venue_wide: bool, after_reservations: bool) -> None:
        """Create the demo closings of one kind, expanding each date spec and resolving the
        service names it targets.

        ``venue_wide`` selects the closings that name no service — they close every service of
        the venue, so they are seeded last, once the bounded services exist too.
        ``after_reservations`` selects the closings flagged to be made once the bookings exist.
        """
        for venue in self._venues.venues:
            venue_id = self._venue_ids.get(venue.key)
            if venue_id is None:
                continue
            for closing in venue.closings:
                if (not closing.services) != venue_wide:
                    continue
                if closing.after_reservations != after_reservations:
                    continue
                service_ids = self._closing_service_ids(venue.key, closing.services)
                if not service_ids:
                    _logger.warning(
                        "Skipping closing on venue [%s]: no matching services.", venue.key
                    )
                    continue
                for date_from, date_to in _expand_dates(closing.dates):
                    await self._create_closing_on(
                        venue_id, venue.key, closing.description, service_ids, date_from, date_to,
                    )

    def _closing_service_ids(self, venue_key: str, names: list[str]) -> list[str]:
        """The service ids a closing targets: those named, or every service of the venue when no
        name is given (a venue-wide shutdown)."""
        if not names:
            return [
                service_id
                for (key, _name), periods in self._service_ids.items()
                if key == venue_key
                for (_date_from, _date_to, service_id) in periods
            ]
        ids: list[str] = []
        for name in names:
            periods = self._service_ids.get((venue_key, name))
            if periods is None:
                _logger.warning(
                    "Closing on venue [%s] names unknown service [%s].", venue_key, name
                )
                continue
            ids.extend(service_id for (_date_from, _date_to, service_id) in periods)
        return ids

    async def _create_closing_on(
            self,
            venue_id: str,
            venue_key: str,
            description: str | None,
            service_ids: list[str],
            date_from: date,
            date_to: date,
    ) -> None:
        """Create one occurrence of a demo closing."""
        payload = {
            "date_from": date_from.isoformat(),
            "date_to": date_to.isoformat(),
            "service_ids": service_ids,
            "description": description,
        }
        await self._write_with_authz_retry(
            lambda: reservation_client.client.post(f"/venues/{venue_id}/closings", json=payload),
            f"closing for [{venue_key}]",
        )
        self._closing_count += 1
        _logger.info(
            "Created closing on [%s]: %s to %s over %d service(s).",
            venue_key, date_from, date_to, len(service_ids),
        )

    async def _create_reservations(self) -> None:
        """Create every demo booking against the service it names.

        The requested time is posted as-is: with no slot grid, any minute inside the service's
        window is bookable, so there is nothing to search for. An occurrence the backend refuses
        — a past date, a closed day, an unknown venue or service, a full service — is skipped and
        counted rather than failing the run.
        """
        for reservation in self._reservations.reservations:
            venue_id = self._venue_ids.get(reservation.venue)
            if venue_id is None:
                _logger.warning(
                    "Skipping reservation for unknown venue key [%s].", reservation.venue
                )
                self._reservation_skipped += 1
                continue
            for start, _end in _expand_dates(reservation.dates):
                await self._create_reservation_on(venue_id, reservation, start)

    def _service_for(self, reservation: DemoReservation, on_date: date) -> str | None:
        """The id of the booking's service covering ``on_date``, or None when none does."""
        periods = self._service_ids.get((reservation.venue, reservation.service))
        if not periods:
            return None
        for date_from, date_to, service_id in periods:
            if date_from <= on_date and (date_to is None or on_date <= date_to):
                return service_id
        return None

    async def _create_reservation_on(
            self, venue_id: str, reservation: DemoReservation, on_date: date,
    ) -> None:
        """Create one occurrence of a demo booking on ``on_date``, or skip it."""
        if on_date < date.today():
            self._reservation_skipped += 1
            return

        service_id = self._service_for(reservation, on_date)
        if service_id is None:
            _logger.info(
                "Skipping reservation for [%s] on %s: service [%s] does not run then.",
                reservation.contact_name,
                on_date,
                reservation.service,
            )
            self._reservation_skipped += 1
            return

        reservation_date = datetime.combine(
            on_date, time.fromisoformat(reservation.time)
        ).isoformat()
        try:
            response = await reservation_client.client.post(
                "/reservations",
                json={
                    "venue_id": venue_id,
                    "service_id": service_id,
                    "contact_name": reservation.contact_name,
                    "contact_phone_number": reservation.contact_phone_number,
                    "contact_email": reservation.contact_email,
                    "party_size": reservation.party_size,
                    "reservation_date": reservation_date,
                    "notes": reservation.notes,
                },
            )
        except HTTPException as exc:
            if exc.status_code != HTTPStatus.CONFLICT:
                raise
            # Closed that date, outside the window, or out of seats — all legitimate reasons a
            # demo booking cannot land, and none worth failing the whole run over.
            _logger.info(
                "Skipping reservation for [%s] on %s: %s",
                reservation.contact_name,
                on_date,
                exc.detail,
            )
            self._reservation_skipped += 1
            return

        reservation_id = response.json()["id"]
        self._reservation_count += 1
        _logger.info(
            "Created reservation for [%s] at %s -> %s",
            reservation.contact_name,
            reservation_date,
            reservation_id,
        )
        await self._apply_reservation_status(reservation_id, reservation.status)


    async def _delete_services(self) -> None:
        """Delete the services the demo data marks as deleted. This runs after the bookings are
        made, since a deleted service takes no new bookings."""
        for service_id, name in self._services_to_delete:
            await self._write_with_authz_retry(
                lambda sid=service_id: reservation_client.client.delete(f"/services/{sid}"),
                f"deletion of [{name}]",
            )
            self._deleted_count += 1
            _logger.info("Deleted service [%s] -> %s", name, service_id)

    async def _apply_reservation_status(self, reservation_id: str, status: str | None) -> None:
        """Move a freshly created booking out of ``pending``, when the demo data asks for it.

        The action authorizes against the RESERVATION resource, whose authz node is created
        reactively from the event the booking published — so this fires before that has landed
        and needs the same retry as the schedule writes.
        """
        if status is None:
            return
        action = _RESERVATION_STATUS_ACTIONS.get(status)
        if action is None:
            _logger.warning("Unknown demo reservation status [%s]; leaving pending.", status)
            return
        await self._write_with_authz_retry(
            lambda: reservation_client.client.post(
                f"/reservations/{reservation_id}/actions", json={"action": action},
            ),
            f"Reservation action [{action}]",
        )

    async def _activate_venues(self) -> None:
        """Activate every venue that has at least one service (a prerequisite for activation)."""
        for key, venue_id in self._venue_ids.items():
            if venue_id not in self._venues_with_services:
                _logger.warning(
                    "Skipping activation of venue [%s]: no services configured.", key
                )
                continue
            await venue_client.client.post(
                f"/venues/{venue_id}/actions",
                json={"action_type": "activate"},
            )
            _logger.info("Activated venue [%s].", key)

    async def _grant_roles(self) -> None:
        """Grant each assignment's role to its users on the referenced venue."""
        for assignment in self._assignments.assignments:
            venue_id = self._venue_ids.get(assignment.venue)
            if venue_id is None:
                _logger.warning(
                    "Skipping assignment for unknown venue key [%s].", assignment.venue
                )
                continue
            for username in assignment.usernames:
                user_id = self._user_ids.get(username)
                if user_id is None:
                    _logger.warning(
                        "Skipping grant for unknown user [%s].", username
                    )
                    continue
                await self._grant_with_retry(venue_id, user_id, assignment.role_id)
                _logger.info(
                    "Granted [%s] to [%s] on venue [%s].",
                    assignment.role_id,
                    username,
                    assignment.venue,
                )

    async def _grant_with_retry(self, venue_id: str, user_id: str, role_id: str) -> None:
        """Grant a venue role, retrying on 404 to absorb Redis propagation lag."""
        for attempt in range(1, _GRANT_MAX_ATTEMPTS + 1):
            try:
                await authz_client.client.post(
                    f"/resources/venue/{venue_id}/acl",
                    json={"user_id": user_id, "role_id": role_id},
                )
                return
            except HTTPException as exc:
                if exc.status_code != HTTPStatus.NOT_FOUND or attempt == _GRANT_MAX_ATTEMPTS:
                    raise
                delay = _GRANT_BACKOFF_BASE_S * 2 ** (attempt - 1)
                _logger.info(
                    "Grant not ready (attempt %d/%d), retrying in %.1fs...",
                    attempt,
                    _GRANT_MAX_ATTEMPTS,
                    delay,
                )
                await asyncio.sleep(delay)

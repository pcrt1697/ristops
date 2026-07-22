import asyncio
import logging
from datetime import date, timedelta
from http import HTTPStatus
from typing import Awaitable, Callable

from fastapi import HTTPException

from ristops_batch_demo.seed.models import (
    DemoAssignments, DemoExceptionDates, DemoService, DemoServices, DemoUsers, DemoVenues,
)
from ristops_batch_demo.services.http import (
    authn_client, authz_client, reservation_client, venue_client,
)
from ristops_lib_core.context import APP_CONTEXT, ContextKey

_logger = logging.getLogger(__name__)


def _expand_exception_dates(anchor: DemoExceptionDates) -> list[tuple[date, date]]:
    """Materialize a calendar exception's date spec into concrete `(start, end)` ranges,
    computed relative to today so the demo data stays near "now" whenever it is seeded."""
    today = date.today()
    if anchor.days_from_now_start is not None and anchor.days_from_now_end is not None:
        return [(
            today + timedelta(days=anchor.days_from_now_start),
            today + timedelta(days=anchor.days_from_now_end),
        )]
    start_month, start_day = (int(part) for part in anchor.month_day_start.split("-"))
    end_month, end_day = (int(part) for part in anchor.month_day_end.split("-"))
    return [
        (
            date(today.year + offset, start_month, start_day),
            date(today.year + offset, end_month, end_day),
        )
        for offset in anchor.year_offsets
    ]

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
            assignments: DemoAssignments,
            admin_email: str,
            admin_password: str,
    ) -> None:
        self._users = users
        self._venues = venues
        self._services = services
        self._assignments = assignments
        self._admin_email = admin_email
        self._admin_password = admin_password
        self._user_ids: dict[str, str] = {}
        self._venue_ids: dict[str, str] = {}
        # Venue ids that received at least one service, and so may be activated.
        self._venues_with_services: set[str] = set()
        self._service_count = 0
        self._override_count = 0
        self._closing_count = 0
        self._capacity_override_count = 0
        self._venue_closing_count = 0

    async def run(self) -> None:
        """Log in as admin, create users, venues, and services, grant roles, and activate."""
        await self._login_as_admin()
        await self._create_users()
        await self._create_venues()
        await self._create_services()
        await self._create_venue_closings()
        await self._grant_roles()
        await self._activate_venues()
        _logger.info(
            "Demo seed complete: %d users, %d venues, %d services, %d overrides, "
            "%d closings, %d capacity overrides, %d venue closings.",
            len(self._user_ids),
            len(self._venue_ids),
            self._service_count,
            self._override_count,
            self._closing_count,
            self._capacity_override_count,
            self._venue_closing_count,
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

    async def _create_services(self) -> None:
        """Create every demo service under its venue, resolving the venue by symbolic key."""
        for service in self._services.services:
            venue_id = self._venue_ids.get(service.venue)
            if venue_id is None:
                _logger.warning(
                    "Skipping service [%s] for unknown venue key [%s].",
                    service.name,
                    service.venue,
                )
                continue
            response = await reservation_client.client.post(
                "/services",
                json={
                    "venue_id": venue_id,
                    "name": service.name,
                    "description": service.description,
                    "turn_time_m": service.turn_time_m,
                    "advance_notice_m": service.advance_notice_m,
                    "slot_interval_m": service.slot_interval_m,
                    "grace_period_m": service.grace_period_m,
                },
            )
            service_id = response.json()["id"]
            self._venues_with_services.add(venue_id)
            self._service_count += 1
            _logger.info(
                "Created service [%s] on venue [%s] -> %s",
                service.name,
                service.venue,
                service_id,
            )
            await self._upsert_openings(service_id, service)
            await self._create_overrides(service_id, service)
            await self._create_closings(service_id, service)
            await self._create_capacity_overrides(service_id, service)

    async def _schedule_write_with_retry(
            self,
            do_request: Callable[[], Awaitable[object]],
            label: str,
    ) -> None:
        """Run a `schedule:*` write, retrying on 403/404 to absorb authz propagation lag.

        These endpoints authorize against the SERVICE resource, whose authz node and venue
        link propagate asynchronously over Redis after the service is created. Until that
        lands the ReBAC check finds no granting path and denies (403), so we retry with
        backoff — mirroring ``_grant_with_retry``'s tolerance for the same lag.
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
        await self._schedule_write_with_retry(
            lambda: reservation_client.client.put(f"/services/{service_id}/openings", json=body),
            f"openings for [{service.name}]",
        )
        _logger.info(
            "Set %d weekly openings on service [%s].", len(service.openings), service.name
        )

    async def _create_overrides(self, service_id: str, service: DemoService) -> None:
        """Create the calendar opening overrides for a service, expanding each date spec."""
        for override in service.overrides:
            for date_start, date_end in _expand_exception_dates(override.dates):
                payload = {
                    "date_start": date_start.isoformat(),
                    "date_end": date_end.isoformat(),
                    "weekdays": [override.weekday] if override.weekday else None,
                    "capacity": override.capacity,
                    "start_time": override.start_time,
                    "end_time": override.end_time,
                    "description": override.description,
                }
                await self._schedule_write_with_retry(
                    lambda p=payload: reservation_client.client.post(
                        f"/services/{service_id}/opening-overrides", json=p
                    ),
                    f"override for [{service.name}]",
                )
                self._override_count += 1
                _logger.info(
                    "Created override on [%s]: %s to %s.",
                    service.name, date_start, date_end,
                )

    async def _create_closings(self, service_id: str, service: DemoService) -> None:
        """Create the calendar closings for a service, expanding each date spec."""
        for closing in service.closings:
            for date_start, date_end in _expand_exception_dates(closing.dates):
                payload = {
                    "date_start": date_start.isoformat(),
                    "date_end": date_end.isoformat(),
                    "weekdays": [closing.weekday] if closing.weekday else None,
                    "description": closing.description,
                }
                await self._schedule_write_with_retry(
                    lambda p=payload: reservation_client.client.post(
                        f"/services/{service_id}/closings", json=p
                    ),
                    f"closing for [{service.name}]",
                )
                self._closing_count += 1
                _logger.info(
                    "Created closing on [%s]: %s to %s.",
                    service.name, date_start, date_end,
                )

    async def _create_capacity_overrides(self, service_id: str, service: DemoService) -> None:
        """Create the calendar capacity overrides for a service, expanding each date spec."""
        for capacity_override in service.capacity_overrides:
            for date_start, date_end in _expand_exception_dates(capacity_override.dates):
                payload = {
                    "date_start": date_start.isoformat(),
                    "date_end": date_end.isoformat(),
                    "weekdays": [capacity_override.weekday] if capacity_override.weekday else None,
                    "capacity_delta": capacity_override.capacity_delta,
                    "description": capacity_override.description,
                }
                await self._schedule_write_with_retry(
                    lambda p=payload: reservation_client.client.post(
                        f"/services/{service_id}/capacity-overrides", json=p
                    ),
                    f"capacity override for [{service.name}]",
                )
                self._capacity_override_count += 1
                _logger.info(
                    "Created capacity override on [%s]: %s to %s.",
                    service.name, date_start, date_end,
                )

    async def _create_venue_closings(self) -> None:
        """Create the venue-wide closings for every demo venue, expanding each date spec."""
        for venue in self._venues.venues:
            venue_id = self._venue_ids.get(venue.key)
            if venue_id is None:
                continue
            for closing in venue.closings:
                for date_start, date_end in _expand_exception_dates(closing.dates):
                    payload = {
                        "date_start": date_start.isoformat(),
                        "date_end": date_end.isoformat(),
                        "weekdays": [closing.weekday] if closing.weekday else None,
                        "description": closing.description,
                    }
                    await self._schedule_write_with_retry(
                        lambda p=payload, vid=venue_id: reservation_client.client.post(
                            f"/venues/{vid}/closings", json=p
                        ),
                        f"venue closing for [{venue.name}]",
                    )
                    self._venue_closing_count += 1
                    _logger.info(
                        "Created venue closing on [%s]: %s to %s.",
                        venue.name, date_start, date_end,
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

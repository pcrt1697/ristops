import asyncio
import logging
from http import HTTPStatus

from fastapi import HTTPException

from ristops_batch_demo.seed.models import DemoAssignments, DemoUsers, DemoVenues
from ristops_batch_demo.services.http import authn_client, authz_client, venue_client
from ristops_lib_core.context import APP_CONTEXT, ContextKey

_logger = logging.getLogger(__name__)

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
            assignments: DemoAssignments,
            admin_email: str,
            admin_password: str,
    ) -> None:
        self._users = users
        self._venues = venues
        self._assignments = assignments
        self._admin_email = admin_email
        self._admin_password = admin_password
        self._user_ids: dict[str, str] = {}
        self._venue_ids: dict[str, str] = {}

    async def run(self) -> None:
        """Log in as admin, create users and venues, then grant venue roles."""
        await self._login_as_admin()
        await self._create_users()
        await self._create_venues()
        await self._grant_roles()
        _logger.info(
            "Demo seed complete: %d users, %d venues.",
            len(self._user_ids),
            len(self._venue_ids),
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

from httpx import AsyncClient

from ristops_be_venue.services.http import authz_client
from ristops_lib_be.authz.client import CheckAuthorizationPolicy


def authz_client_factory() -> AsyncClient:
    return authz_client.client


is_authorized = CheckAuthorizationPolicy(authz_client_factory)

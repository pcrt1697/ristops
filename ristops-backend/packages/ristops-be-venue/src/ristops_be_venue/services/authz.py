from httpx import AsyncClient

from ristops_be_authn.services.http import http_service, HttpClient
from ristops_lib_be.authz.client import CheckAuthorizationPolicy


def authz_client_factory() -> AsyncClient:
    return http_service.get(HttpClient.AUTHZ)


is_authorized = CheckAuthorizationPolicy(authz_client_factory)

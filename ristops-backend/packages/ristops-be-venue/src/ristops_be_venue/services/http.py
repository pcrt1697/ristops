from enum import StrEnum

from ristops_be_venue.settings import BackendServiceSettings
from ristops_lib_core.http import HttpClientService


class HttpClient(StrEnum):
    AUTHN = "authn"
    AUTHZ = "authz"


http_service = HttpClientService[HttpClient]()


def get_http_clients() -> dict[HttpClient, str]:
    be_settings = BackendServiceSettings.get()
    clients = {
        HttpClient.AUTHN: be_settings.authn_url,
        HttpClient.AUTHZ: be_settings.authz_url,
    }
    return clients

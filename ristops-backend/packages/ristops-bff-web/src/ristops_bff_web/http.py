from enum import StrEnum

from ristops_lib_core.http import HttpClientService


class HttpClient(StrEnum):
    AUTHN = "authn"
    AUTHZ = "authz"
    VENUE = "venue"


http_service = HttpClientService[HttpClient]()

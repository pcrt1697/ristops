from enum import StrEnum

from ristops_lib_core.http import HttpClientService


class HttpClient(StrEnum):
    AUTHN = "authn"


http_service = HttpClientService[HttpClient]()

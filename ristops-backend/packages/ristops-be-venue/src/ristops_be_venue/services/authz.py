import logging

from ristops_be_venue.services.http import http_service, HttpClient
from ristops_lib_core.schema.authz import (
    CheckAuthorizationRequest
)

_logger = logging.getLogger(__name__)


async def is_authorized(request: CheckAuthorizationRequest) -> bool:
    _user = await http_service.get(HttpClient.AUTHZ).post(
        url=f"/acl/check",
        json=request.model_dump(mode="json")
    )
    return _user.json().get("is_authorized", False)

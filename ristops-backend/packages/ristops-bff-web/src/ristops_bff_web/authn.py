import logging
import time

from jwt import ExpiredSignatureError
from starlette import status
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from starsessions import load_session

from ristops_bff_web.domain.auth.service import refresh_access_token
from ristops_bff_web.session import update_context, SessionField
from ristops_lib_core.auth.authn import AuthNMiddleware, JwtDecoder, PublicRoutesRegistry
from ristops_lib_core.exception import create_error_response

_logger = logging.getLogger(__name__)


async def _decode_jwt_and_update_context(request: Request, jwt_decoder: JwtDecoder) -> None:
    try:
        token = request.session[SessionField.ACCESS_TOKEN]
        payload = jwt_decoder(token)
        expires_in = payload["exp"] - int(time.time())
        if expires_in >= 60:
            update_context(request)
        else:
            # expires within 60 seconds -> early refresh
            _logger.debug("Early refreshing JWT")
            await refresh_access_token(request.session[SessionField.REFRESH_TOKEN], request)
    except ExpiredSignatureError:
        _logger.debug("Refreshing expired JWT")
        await refresh_access_token(request.session[SessionField.REFRESH_TOKEN], request)


class SessionAuthNMiddleware(AuthNMiddleware):
    """
    Session authentication middleware.
    All graphql requests are considered non-public.
    """

    def __init__(self, app: ASGIApp, public_registry: PublicRoutesRegistry, jwt_decoder: JwtDecoder) -> None:
        super().__init__(app, public_registry)
        self._jwt_decoder = jwt_decoder

    async def _dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        await load_session(request)
        if request.session.get(SessionField.USER_ID) is None:
            return create_error_response(
                http_status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            await _decode_jwt_and_update_context(request, self._jwt_decoder)
        except Exception as e:
            request.session.clear()  # wipe invalid session
            _logger.exception("Failed to decode JWT payload %s", e.__class__)
            return create_error_response(
                http_status=status.HTTP_401_UNAUTHORIZED,
                content="Invalid credentials",
            )
        return await call_next(request)

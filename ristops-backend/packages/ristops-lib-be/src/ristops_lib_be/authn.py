import logging

from fastapi import FastAPI
from starlette import status
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from ristops_lib_core.auth.authn import JwtDecoder, AuthNMiddleware
from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.exception import create_error_response

_logger = logging.getLogger(__name__)


class JwtAuthNMiddleware(AuthNMiddleware):
    """ Middleware used to authenticate requests """

    def __init__(self, app: ASGIApp, api: FastAPI, jwt_decoder: JwtDecoder) -> None:
        super().__init__(app, api)
        self._jwt_decoder = jwt_decoder

    async def _dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            _logger.error("Invalid JWT authorization header: %s", auth_header)
            return create_error_response(
                http_status=status.HTTP_401_UNAUTHORIZED,
                content="Invalid credentials",
            )

        token = auth_header.removeprefix("Bearer ")
        APP_CONTEXT.set(ContextKey.JWT, token)
        try:
            payload = self._jwt_decoder(token)
            APP_CONTEXT.set(ContextKey.USER_ID, payload['sub'])
        except Exception as e:
            _logger.exception("Failed to decode JWT payload %s", e.__class__)
            return create_error_response(
                http_status=status.HTTP_401_UNAUTHORIZED,
                content="Invalid credentials",
            )
        return await call_next(request)

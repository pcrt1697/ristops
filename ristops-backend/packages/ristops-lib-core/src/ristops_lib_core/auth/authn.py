from abc import ABC, abstractmethod
from enum import StrEnum
from http import HTTPMethod
from typing import Callable, TypedDict
from uuid import UUID

import jwt
from fastapi import FastAPI
from jwt import PyJWKClient, InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from ristops_lib_core.app.routes import RouteAttributeRegistry

AUTH_ALGORITHM = "ES256"
IS_PUBLIC = "_is_public"
DEFAULT_ADMIN_USERNAME = "ristops"
RISTOPS_NAMESPACE_UUID = UUID("57cf6b1c-32ca-49d7-bfcc-7299388df6f3")


def public(route_func: Callable) -> Callable:
    """ Mark a route as public (no auth required). """
    setattr(route_func, IS_PUBLIC, True)
    return route_func


class TokenType(StrEnum):
    REFRESH = "refresh"
    ACCESS = "access"


class JwtPayload(TypedDict):
    sub: str
    exp: int
    iat: int
    token_type: TokenType


JwtDecoder = Callable[[str], JwtPayload]


class InvalidTokenTypeError(InvalidTokenError):
    pass


def decode_jwt(token: str, key: bytes, expected_type: TokenType) -> JwtPayload:
    payload: JwtPayload = jwt.decode(token, key, algorithms=[AUTH_ALGORITHM])
    if (token_type := payload.get("token_type")) != expected_type:
        raise InvalidTokenTypeError(f"Invalid token type: expected {expected_type}, found {token_type}")
    return payload


class ClientTokenDecoder:

    def __init__(self, auth_service_url: str) -> None:
        self._jwks_client = PyJWKClient(
            f"{auth_service_url}/.well-known/jwks.json",
            cache_keys=True,
        )

    def __call__(self, token: str) -> JwtPayload:
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        return decode_jwt(token, signing_key.key, TokenType.ACCESS)


class AuthNMiddleware(BaseHTTPMiddleware, ABC):
    """ Middleware used to authenticate requests """

    def __init__(self, app: ASGIApp, public_registry: PublicRoutesRegistry) -> None:
        super().__init__(app)
        self._public_registry = public_registry

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if self._public_registry.is_public(request):
            return await call_next(request)
        return await self._dispatch(request, call_next)

    @abstractmethod
    async def _dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        pass


class PublicRoutesRegistry:

    def __init__(self, api: FastAPI) -> None:
        self._public_routes = RouteAttributeRegistry[bool | None](api, IS_PUBLIC)
        self._public_paths: set[tuple[str, str]] = set()
        if api.openapi_url is not None:
            self._public_paths.add((HTTPMethod.GET.lower(), api.root_path + api.openapi_url))
        if api.docs_url:
            self._public_paths.add((HTTPMethod.GET.lower(), api.docs_url))

    def is_public(self, request: Request) -> bool:
        if (request.method.lower(), request.url.path) in self._public_paths:
            return True
        return self._public_routes.get(request.scope) or False

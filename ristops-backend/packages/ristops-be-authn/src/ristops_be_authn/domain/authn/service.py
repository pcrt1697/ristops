import base64
import hashlib
import json
import logging
import time
from functools import lru_cache
from typing import Any
from uuid import UUID

import jwt
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from fastapi import HTTPException
from jwt.algorithms import ECAlgorithm
from starlette import status

from ristops_be_authn.domain.authn.schema import JWKResponse, JWK
from ristops_be_authn.domain.user.service import authenticate_user, throw_if_user_not_exists
from ristops_be_authn.settings import JwtSettings
from ristops_lib_core.auth.authn import AUTH_ALGORITHM, JwtPayload, TokenType, decode_jwt
from ristops_lib_core.context import APP_CONTEXT, ContextKey
from ristops_lib_core.schema.authn import LoginResponse, LoginRequest

_logger = logging.getLogger(__name__)


def generate_kid(jwk: dict) -> str:
    """Generate a key ID using RFC 7638 thumbprint."""
    canonical = json.dumps(
        {k: jwk[k] for k in sorted(["crv", "kty", "x", "y"])},
        separators=(",", ":"),
        sort_keys=True,
    )
    digest = hashlib.sha256(canonical.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def key_to_jwk(key) -> dict[str, Any]:
    jwk = ECAlgorithm.to_jwk(key)  # type: ignore
    if isinstance(jwk, str):
        jwk = json.loads(jwk)
    return jwk  # type: ignore


@lru_cache(maxsize=1)
def build_jwks() -> JWKResponse:
    jwk = _get_public_jwk()
    kid = generate_kid(jwk)
    _jwk = {
               "use": "sig",
               "alg": "ES256",
               "kid": kid,
           } | jwk
    return JWKResponse(
        keys=[
            JWK.model_validate(_jwk),
        ]
    )


@lru_cache(maxsize=1)
def _get_private_key() -> tuple[bytes, int]:
    settings = JwtSettings.get()
    return settings.private_key_location.read_bytes(), int(settings.access_expiration_m * 60)


@lru_cache(maxsize=1)
def _get_refresh_key() -> tuple[bytes, int]:
    settings = JwtSettings.get()
    return settings.refresh_key_location.read_bytes(), int(settings.refresh_expiration_h * 3600)


@lru_cache(maxsize=1)
def _get_public_jwk() -> dict[str, Any]:
    settings = JwtSettings.get()
    pem = settings.public_key_location.read_bytes()
    key = load_pem_public_key(pem)
    jwk = ECAlgorithm.to_jwk(key)  # type: ignore
    if isinstance(jwk, str):
        jwk = json.loads(jwk)
    return jwk


def _generate_token(
        user_id: str,
        key: bytes,
        exp_after: int,
        token_type: TokenType,
        kid: str = None,
) -> str:
    iat = int(time.time())
    exp = iat + exp_after
    payload: JwtPayload = {
        "sub": user_id,
        "iat": iat,
        "exp": exp,
        "token_type": token_type,
    }
    headers = None if kid is None else {"kid": kid}
    return jwt.encode(
        payload,
        key,
        algorithm=AUTH_ALGORITHM,
        headers=headers
    )


def _generate_access_token(user_id: str) -> str:
    private_key, exp = _get_private_key()
    jwk = _get_public_jwk()
    kid = generate_kid(jwk)
    return _generate_token(
        user_id=user_id,
        key=private_key,
        exp_after=exp,
        token_type=TokenType.ACCESS,
        kid=kid,
    )


def _generate_refresh_token(user_id: str) -> str:
    key, exp = _get_refresh_key()
    return _generate_token(
        user_id=user_id,
        key=key,
        exp_after=exp,
        token_type=TokenType.REFRESH,
    )


def _generate_tokens(user_id: str) -> LoginResponse:
    access_token = _generate_access_token(user_id)
    APP_CONTEXT.set(ContextKey.JWT, access_token)
    refresh_token = _generate_refresh_token(user_id)
    return LoginResponse(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def perform_login(request: LoginRequest) -> LoginResponse:
    user_id = await authenticate_user(request.email, request.password)
    response = _generate_tokens(user_id)
    APP_CONTEXT.set(ContextKey.USER_ID, user_id)
    return response


def decode_access_token(access_token: str) -> JwtPayload:
    key, _ = _get_private_key()
    return decode_jwt(access_token, key, TokenType.ACCESS)


async def refresh_access_token(refresh_token: str) -> LoginResponse:
    key, _ = _get_refresh_key()
    try:
        payload = decode_jwt(refresh_token, key, TokenType.REFRESH)
    except Exception as exc:
        _logger.exception(f"Failed to decode refresh token: {exc.__class__}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")
    await throw_if_user_not_exists(UUID(payload["sub"]))
    return _generate_tokens(payload["sub"])

from fastapi import APIRouter

from ristops_be_authn.domain.authn.schema import JWKResponse
from ristops_be_authn.domain.authn.service import perform_login, build_jwks, refresh_access_token
from ristops_lib_core.auth.authn import public
from ristops_lib_core.schema.authn import RefreshTokenRequest, LoginResponse, LoginRequest
from ristops_lib_sql.engine import sql_transactional

auth_router = APIRouter(
    tags=["auth"],
)


@auth_router.post(
    "/auth/login",
    response_model=LoginResponse,
)
@public
@sql_transactional
async def login(request: LoginRequest) -> LoginResponse:
    return await perform_login(request)


@auth_router.post(
    "/auth/refresh",
    response_model=LoginResponse,
)
@public
@sql_transactional
async def refresh(request: RefreshTokenRequest) -> LoginResponse:
    return await refresh_access_token(request.refresh_token)


@auth_router.get(
    "/.well-known/jwks.json",
    response_model=JWKResponse,
    description=(
        "Returns the public key set used to verify JWT access tokens. "
        "The response is cached in memory for the lifetime of the process. "
        "Key rotation requires a service restart."
    ),
)
@public
async def jwks() -> JWKResponse:
    return build_jwks()

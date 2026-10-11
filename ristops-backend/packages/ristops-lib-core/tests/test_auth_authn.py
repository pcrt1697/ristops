import jwt
import pytest
from fastapi import APIRouter, FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

import ristops_lib_core.auth.authn as authn
from helpers import make_client, make_ec_key_pair, make_scope, make_token
from ristops_lib_core.auth.authn import (
    AUTH_ALGORITHM, IS_PUBLIC, AuthNMiddleware, ClientTokenDecoder, InvalidTokenTypeError, PublicRoutesRegistry,
    TokenType, decode_jwt, public,
)


@pytest.fixture(scope="module")
def keys() -> tuple[bytes, bytes]:
    return make_ec_key_pair()


def test_constants():
    assert AUTH_ALGORITHM == "ES256"
    assert IS_PUBLIC == "_is_public"
    assert {TokenType.ACCESS, TokenType.REFRESH} == {"access", "refresh"}


class TestPublicDecorator:

    def test_marks_the_function_and_returns_it_unchanged(self):
        async def route() -> None: ...

        assert public(route) is route
        assert getattr(route, IS_PUBLIC) is True

    def test_an_undecorated_function_has_no_mark(self):
        async def route() -> None: ...

        assert not hasattr(route, IS_PUBLIC)


class TestDecodeJwt:

    def test_returns_the_payload_of_a_valid_token(self, keys):
        private, public_key = keys

        payload = decode_jwt(make_token(private, sub="alice"), public_key, TokenType.ACCESS)

        assert payload["sub"] == "alice"
        assert payload["token_type"] == "access"

    def test_rejects_a_token_of_the_wrong_type(self, keys):
        private, public_key = keys

        with pytest.raises(InvalidTokenTypeError, match="expected access, found refresh"):
            decode_jwt(make_token(private, token_type="refresh"), public_key, TokenType.ACCESS)

    def test_a_refresh_token_is_accepted_when_refresh_is_expected(self, keys):
        private, public_key = keys

        assert decode_jwt(make_token(private, token_type="refresh"), public_key, TokenType.REFRESH)["sub"] == "user-1"

    def test_rejects_a_token_without_a_type(self, keys):
        private, public_key = keys

        with pytest.raises(InvalidTokenTypeError):
            decode_jwt(make_token(private, token_type=None), public_key, TokenType.ACCESS)

    def test_invalid_token_type_is_an_invalid_token_error(self):
        assert issubclass(InvalidTokenTypeError, jwt.InvalidTokenError)

    def test_rejects_an_expired_token(self, keys):
        private, public_key = keys

        with pytest.raises(jwt.ExpiredSignatureError):
            decode_jwt(make_token(private, expires_in=-60), public_key, TokenType.ACCESS)

    def test_rejects_a_token_signed_with_another_key(self, keys):
        _, public_key = keys
        other_private, _ = make_ec_key_pair()

        with pytest.raises(jwt.InvalidSignatureError):
            decode_jwt(make_token(other_private), public_key, TokenType.ACCESS)

    def test_rejects_a_token_that_uses_another_algorithm(self, keys):
        _, public_key = keys
        token = jwt.encode({"sub": "user-1", "token_type": "access"}, "a-shared-secret-of-sufficient-length", "HS256")

        with pytest.raises(jwt.InvalidAlgorithmError):
            decode_jwt(token, public_key, TokenType.ACCESS)

    def test_rejects_garbage(self, keys):
        _, public_key = keys

        with pytest.raises(jwt.DecodeError):
            decode_jwt("not-a-token", public_key, TokenType.ACCESS)


class TestClientTokenDecoder:

    @pytest.fixture
    def fake_jwk_client(self, monkeypatch: pytest.MonkeyPatch, keys):
        _, public_key = keys
        created = []

        class FakeSigningKey:
            key = public_key

        class FakeJwkClient:
            def __init__(self, url: str, cache_keys: bool) -> None:
                self.url, self.cache_keys, self.tokens = url, cache_keys, []
                created.append(self)

            def get_signing_key_from_jwt(self, token: str) -> FakeSigningKey:
                self.tokens.append(token)
                return FakeSigningKey()

        monkeypatch.setattr(authn, "PyJWKClient", FakeJwkClient)
        return created

    def test_reads_the_keys_from_the_well_known_jwks_url_and_caches_them(self, fake_jwk_client):
        ClientTokenDecoder("http://authn:8001/api")

        assert fake_jwk_client[0].url == "http://authn:8001/api/.well-known/jwks.json"
        assert fake_jwk_client[0].cache_keys is True

    def test_decodes_an_access_token(self, fake_jwk_client, keys):
        private, _ = keys
        token = make_token(private, sub="alice")

        payload = ClientTokenDecoder("http://authn")(token)

        assert payload["sub"] == "alice"
        assert fake_jwk_client[0].tokens == [token]

    def test_rejects_a_refresh_token(self, fake_jwk_client, keys):
        private, _ = keys

        with pytest.raises(InvalidTokenTypeError):
            ClientTokenDecoder("http://authn")(make_token(private, token_type="refresh"))


class HeaderAuthN(AuthNMiddleware):
    """Authenticates by the presence of an `x-user` header."""

    async def _dispatch(self, request, call_next):
        if "x-user" not in request.headers:
            return JSONResponse({"detail": "no credentials"}, status_code=401)
        return await call_next(request)


def build_secured_app() -> FastAPI:
    app = FastAPI()
    router = APIRouter(prefix="/api")

    @router.get("/open")
    @public
    async def open_route() -> dict:
        return {"route": "open"}

    @router.get("/closed")
    async def closed_route() -> dict:
        return {"route": "closed"}

    app.include_router(router)

    @app.get("/direct-open")
    @public
    async def direct_open() -> dict:
        return {"route": "direct-open"}

    app.add_middleware(HeaderAuthN, public_registry=PublicRoutesRegistry(app))
    return app


class TestAuthNMiddleware:

    @pytest.mark.anyio
    @pytest.mark.parametrize("path", ["/api/open", "/direct-open"])
    async def test_public_routes_skip_authentication(self, path: str):
        async with make_client(build_secured_app()) as client:
            response = await client.get(path)

        assert response.status_code == 200

    @pytest.mark.anyio
    async def test_other_routes_are_authenticated(self):
        async with make_client(build_secured_app()) as client:
            denied = await client.get("/api/closed")
            allowed = await client.get("/api/closed", headers={"x-user": "alice"})

        assert denied.status_code == 401
        assert allowed.status_code == 200

    @pytest.mark.anyio
    async def test_unknown_routes_are_authenticated_before_they_can_404(self):
        async with make_client(build_secured_app()) as client:
            response = await client.get("/api/nothing")

        assert response.status_code == 401

    def test_cannot_be_used_without_implementing_dispatch(self):
        with pytest.raises(TypeError):
            AuthNMiddleware(FastAPI(), PublicRoutesRegistry(FastAPI()))


def make_request(method: str, path: str) -> Request:
    return Request(make_scope(method, path))


class TestPublicRoutesRegistry:

    def test_marked_routes_are_public_including_nested_ones(self):
        registry = PublicRoutesRegistry(build_secured_app())

        assert registry.is_public(make_request("GET", "/api/open"))
        assert registry.is_public(make_request("GET", "/direct-open"))

    def test_other_routes_are_not_public(self):
        registry = PublicRoutesRegistry(build_secured_app())

        assert not registry.is_public(make_request("GET", "/api/closed"))
        assert not registry.is_public(make_request("GET", "/api/nothing"))

    def test_public_depends_on_the_method(self):
        registry = PublicRoutesRegistry(build_secured_app())

        assert not registry.is_public(make_request("POST", "/api/open"))

    def test_the_schema_and_the_docs_are_public_by_default(self):
        registry = PublicRoutesRegistry(FastAPI())

        assert registry.is_public(make_request("GET", "/openapi.json"))
        assert registry.is_public(make_request("GET", "/docs"))

    def test_the_schema_and_the_docs_are_only_public_for_get(self):
        registry = PublicRoutesRegistry(FastAPI())

        assert not registry.is_public(make_request("POST", "/openapi.json"))
        assert not registry.is_public(make_request("DELETE", "/docs"))

    def test_the_schema_and_the_docs_are_not_public_once_disabled(self):
        registry = PublicRoutesRegistry(FastAPI(openapi_url=None, docs_url=None))

        assert not registry.is_public(make_request("GET", "/openapi.json"))
        assert not registry.is_public(make_request("GET", "/docs"))

    def test_the_schema_url_follows_a_custom_path(self):
        registry = PublicRoutesRegistry(FastAPI(openapi_url="/spec.json"))

        assert registry.is_public(make_request("GET", "/spec.json"))
        assert not registry.is_public(make_request("GET", "/openapi.json"))

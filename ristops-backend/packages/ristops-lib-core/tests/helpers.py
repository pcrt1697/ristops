"""Shared builders and fakes for the lib-core tests."""

import httpx
from fastapi import APIRouter, FastAPI
from opentelemetry.sdk.trace import TracerProvider


def make_tracer():
    """Return a tracer that is not installed globally, so tests can open real spans without touching global state."""
    return TracerProvider().get_tracer("lib-core-tests")


def make_client(app: FastAPI) -> httpx.AsyncClient:
    """Return an async client that calls the app in process."""
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")


MARKER = "_test_marker"


def marker(value):
    """Return a decorator that tags a route function with the given value, the way `@public` and `@policy` do."""

    def decorator(route_func):
        setattr(route_func, MARKER, value)
        return route_func

    return decorator


def make_scope(method: str, path: str) -> dict:
    """Return the minimal ASGI scope of an HTTP request."""
    return {
        "type": "http", "method": method, "path": path, "root_path": "",
        "query_string": b"", "headers": [], "scheme": "http", "server": ("testserver", 80),
    }


def build_marked_app(**app_kwargs) -> FastAPI:
    """Build an app whose routes are registered in every way a service does, each tagged with a marker value.

    Routes: an inner router (prefix `/inner`) included in an outer one (prefix `/api`) included in the app, a route
    on the outer router, a route registered straight on the app, one without a marker, and a sub-application mount.
    """
    app = FastAPI(**app_kwargs)

    inner = APIRouter(prefix="/inner")

    @inner.get("/items/{item_id}")
    @marker("inner-get")
    async def get_item(item_id: str) -> dict:
        return {"item_id": item_id}

    outer = APIRouter(prefix="/api")
    outer.include_router(inner)

    @outer.post("/things")
    @marker("outer-post")
    async def create_thing() -> dict:
        return {}

    @outer.get("/unmarked")
    async def unmarked() -> dict:
        return {}

    app.include_router(outer)

    @app.get("/direct")
    @marker("direct")
    async def direct() -> dict:
        return {}

    @app.api_route("/multi", methods=["GET", "PUT"])
    @marker("multi")
    async def multi() -> dict:
        return {}

    app.mount("/sub", FastAPI())
    return app


def make_ec_key_pair() -> tuple[bytes, bytes]:
    """Return a fresh P-256 key pair as (private PEM, public PEM), the kind be-authn signs its tokens with."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def make_token(private_pem: bytes, token_type: str | None = "access", expires_in: int = 300, **claims) -> str:
    """Sign a JWT the way be-authn does, with ES256."""
    import time

    import jwt

    now = int(time.time())
    payload = {"sub": "user-1", "iat": now, "exp": now + expires_in, **claims}
    if token_type is not None:
        payload["token_type"] = token_type
    return jwt.encode(payload, private_pem, algorithm="ES256")


def install_mock_transport(monkeypatch, handler) -> None:
    """Make every client that `HttpClient` binds talk to `handler` instead of the network."""
    import ristops_lib_core.http as http_module

    real_client = httpx.AsyncClient
    monkeypatch.setattr(
        http_module, "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs),
    )


def fake_entry_points(*entries: tuple[str, str, str]):
    """Return a stand-in for `importlib.metadata.entry_points` that knows only the given entries.

    Each entry is a (group, name, value) tuple.
    """
    from importlib.metadata import EntryPoint, EntryPoints

    available = EntryPoints(EntryPoint(name=name, value=value, group=group) for group, name, value in entries)

    def entry_points(**selection) -> EntryPoints:
        return available.select(**selection)

    return entry_points


def _make_demo_command():
    import click

    @click.command()
    def demo_command() -> None:
        """A command that the lazy loader can import."""
        click.echo("demo ran")

    return demo_command


demo_command = _make_demo_command()
not_a_command = "just a string"


def demo_app_factory() -> str:
    """Stand-in for a service's `create_app`."""
    return "demo-app"

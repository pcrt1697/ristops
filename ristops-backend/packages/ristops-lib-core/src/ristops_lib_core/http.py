import logging
from contextlib import asynccontextmanager, AsyncExitStack, AbstractAsyncContextManager
from copy import deepcopy
from typing import Callable, Awaitable, Any, AsyncGenerator

from fastapi import HTTPException
from httpx import AsyncClient, Request, Response, Headers

from ristops_lib_core.context import APP_CONTEXT, ContextHeader, ContextKey

_logger = logging.getLogger(__name__)


def get_trace_headers(headers: Headers) -> dict[str, str | None]:
    _headers = {}
    if not headers:
        return _headers
    for header in [ContextHeader.CORRELATION_ID, ContextKey.REQUEST_ID]:
        _headers[header] = headers.get(header)
    return _headers


async def inject_trace_headers(request: Request) -> None:
    for header, key in (
            (ContextHeader.CORRELATION_ID, ContextKey.CORRELATION_ID),
            (ContextHeader.REQUEST_ID, ContextKey.REQUEST_ID),
    ):
        value = APP_CONTEXT.get(key)
        if value is not None:
            request.headers[header] = value


async def inject_auth_header(request: Request) -> None:
    token = APP_CONTEXT.get(ContextKey.JWT)
    if token is not None:
        request.headers["Authorization"] = f"Bearer {token}"


async def raise_for_status(response: Response) -> None:
    await response.aread()
    if response.is_success:
        return
    request_trace = get_trace_headers(response.request.headers)
    response_trace = get_trace_headers(response.headers)
    _logger.error(
        "HTTP request failed. %s %s %s -> %s %s %s",
        response.request.method,
        response.request.url,
        request_trace,
        response.status_code,
        response_trace,
        response.content,
    )
    raise HTTPException(
        status_code=response.status_code,
        detail=response.json()
    )


class HttpClient:
    """A single httpx AsyncClient with trace/auth header injection and error raising.

    Bind a base URL for the duration of a context::

        async with client("http://authn"):
            await client.client.get("/users/me")
    """

    def __init__(
            self,
            hooks: dict[str, list[Callable[[Request], Awaitable]]] | None = None,
            timeout: float | None = None,
    ) -> None:
        self._hooks: dict[str, list[Callable]] = deepcopy(hooks or {})
        if "request" not in self._hooks:
            self._hooks["request"] = []
        self._hooks["request"].extend([inject_trace_headers, inject_auth_header])
        if "response" not in self._hooks:
            self._hooks["response"] = []
        self._hooks["response"].append(raise_for_status)
        self._timeout = timeout or 30

        self._delegate: AsyncClient | None = None

    @property
    def client(self) -> AsyncClient:
        """Return the bound AsyncClient, or raise if used outside its context."""
        if self._delegate is not None:
            return self._delegate
        raise RuntimeError("HTTP client not initialized")

    def __call__(self, base_url: str) -> AbstractAsyncContextManager[None]:
        """Bind an AsyncClient against `base_url` for the duration of the context."""
        return self._bind(base_url)

    @asynccontextmanager
    async def _bind(self, base_url: str) -> AsyncGenerator[None]:
        if self._delegate is not None:
            raise RuntimeError("HTTP client is already bound")
        client = AsyncClient(base_url=base_url, event_hooks=self._hooks, timeout=self._timeout)
        self._delegate = client
        try:
            yield
        finally:
            self._delegate = None
            await client.aclose()


@asynccontextmanager
async def with_clients(*clients: tuple[HttpClient, str]) -> AsyncGenerator[None]:
    """Bind each `(client, base_url)` pair for the duration of the context."""
    # noinspection PyAbstractClass
    async with AsyncExitStack() as stack:
        for client, base_url in clients:
            await stack.enter_async_context(client(base_url))
        yield


class ResponseTransformer:
    """Parses configured fields of a JSON object with the given per-field parser functions."""

    def __init__(self, **field_parsers: Callable):
        self._field_parsers = field_parsers

    def transform(self, obj: dict[str, Any]) -> dict[str, Any]:
        """Apply the configured parsers to the matching fields of `obj`, in place."""
        for field_name, parse_func in self._field_parsers.items():
            if (value := obj.get(field_name)) is not None:
                obj[field_name] = parse_func(value)
        return obj

    def get_json(self, response: Response) -> dict[str, Any]:
        """Parse the response body and apply the configured field parsers."""
        return self.transform(response.json())

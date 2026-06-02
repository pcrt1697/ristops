import logging
from contextlib import asynccontextmanager, AsyncExitStack
from copy import deepcopy
from enum import StrEnum
from typing import Callable, Awaitable, Any

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
    response.raise_for_status()


class HttpClientService[T: StrEnum]:
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with http_service():
            yield
    """

    def __init__(
            self,
            hooks: dict[str, list[Callable[[Request], Awaitable]]] = None,
            timeout: float = None,
    ):
        self._clients: dict[T, AsyncClient] = {}
        self._hooks: dict[str, list[Callable]] = deepcopy(hooks or {})
        if "request" not in self._hooks:
            self._hooks["request"] = []
        self._hooks["request"].extend([inject_trace_headers, inject_auth_header])
        if "response" not in self._hooks:
            self._hooks["response"] = []
        self._hooks["response"].append(raise_for_status)
        self._timeout = timeout or 30

    def get(self, name: T) -> AsyncClient:
        if name not in self._clients:
            raise RuntimeError(f"HTTP client '{name}' not initialized")
        return self._clients[name]

    @asynccontextmanager
    async def __call__(self, clients_config: dict[T, str]):
        # noinspection PyAbstractClass
        async with AsyncExitStack() as stack:
            for name, base_url in clients_config.items():
                client = await stack.enter_async_context(
                    AsyncClient(
                        base_url=base_url,
                        event_hooks=self._hooks,
                        timeout=self._timeout,
                    )
                )
                self._clients[name] = client
            yield

        self._clients.clear()


class ResponseTransformer:

    def __init__(self, **field_parsers: Callable):
        self._field_parsers = field_parsers

    def get_json(self, response: Response) -> dict[str, Any]:
        obj = response.json()
        for field_name, parse_func in self._field_parsers.items():
            if (value := obj.get(field_name)) is not None:
                obj[field_name] = parse_func(value)
        return obj

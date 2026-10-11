import logging

import httpx
import pytest
from fastapi import HTTPException

from helpers import install_mock_transport
from ristops_lib_core.context import APP_CONTEXT, ContextHeader, ContextKey
from ristops_lib_core.http import (
    HttpClient, ResponseTransformer, drop_empty_query_params, get_trace_headers, inject_auth_header,
    raise_for_status, with_clients,
)


class TestTraceHeaders:

    def test_no_headers_gives_an_empty_dict(self):
        assert get_trace_headers(httpx.Headers()) == {}

    def test_returns_both_trace_headers(self):
        headers = httpx.Headers({ContextHeader.CORRELATION_ID: "c-1", ContextHeader.REQUEST_ID: "r-1"})

        assert get_trace_headers(headers) == {"x-correlation-id": "c-1", "x-request-id": "r-1"}

    def test_a_missing_trace_header_is_none(self):
        headers = httpx.Headers({ContextHeader.REQUEST_ID: "r-1"})

        assert get_trace_headers(headers) == {"x-correlation-id": None, "x-request-id": "r-1"}

    def test_other_headers_are_ignored(self):
        assert get_trace_headers(httpx.Headers({"x-other": "1"})) == {"x-correlation-id": None, "x-request-id": None}


class TestInjectAuthHeader:

    @pytest.mark.anyio
    async def test_adds_the_bearer_token_from_the_context(self):
        APP_CONTEXT.set(ContextKey.JWT, "token-1")
        request = httpx.Request("GET", "http://service/path")

        await inject_auth_header(request)

        assert request.headers["Authorization"] == "Bearer token-1"

    @pytest.mark.anyio
    async def test_leaves_the_request_alone_without_a_token(self):
        request = httpx.Request("GET", "http://service/path")

        await inject_auth_header(request)

        assert "Authorization" not in request.headers

    @pytest.mark.anyio
    async def test_replaces_an_existing_authorization_header(self):
        APP_CONTEXT.set(ContextKey.JWT, "token-1")
        request = httpx.Request("GET", "http://service/path", headers={"Authorization": "Bearer other"})

        await inject_auth_header(request)

        assert request.headers["Authorization"] == "Bearer token-1"


class TestDropEmptyQueryParams:

    @pytest.mark.anyio
    async def test_drops_params_with_an_empty_value(self):
        request = httpx.Request("GET", "http://service/path?scope=&name=pizza&other=")

        await drop_empty_query_params(request)

        assert dict(request.url.params) == {"name": "pizza"}

    @pytest.mark.anyio
    async def test_keeps_repeated_params_in_order(self):
        request = httpx.Request("GET", "http://service/path?sort=name&sort=-created&skip=")

        await drop_empty_query_params(request)

        assert request.url.params.get_list("sort") == ["name", "-created"]

    @pytest.mark.anyio
    async def test_leaves_a_clean_request_untouched(self):
        request = httpx.Request("GET", "http://service/path?name=pizza")

        await drop_empty_query_params(request)

        assert str(request.url) == "http://service/path?name=pizza"

    @pytest.mark.anyio
    async def test_a_request_with_only_empty_params_loses_its_query(self):
        request = httpx.Request("GET", "http://service/path?scope=")

        await drop_empty_query_params(request)

        assert request.url.query == b""

    @pytest.mark.anyio
    async def test_keeps_zero_and_false_looking_values(self):
        request = httpx.Request("GET", "http://service/path?page=0&flag=false")

        await drop_empty_query_params(request)

        assert dict(request.url.params) == {"page": "0", "flag": "false"}


class TestRaiseForStatus:

    @staticmethod
    def make_response(status: int, **kwargs) -> httpx.Response:
        return httpx.Response(status, request=httpx.Request("GET", "http://service/thing"), **kwargs)

    @pytest.mark.anyio
    async def test_a_successful_response_passes(self):
        assert await raise_for_status(self.make_response(204)) is None

    @pytest.mark.anyio
    async def test_an_error_becomes_an_http_exception_with_the_json_body(self):
        body = {"title": "Not Found", "detail": "no such thing"}

        with pytest.raises(HTTPException) as caught:
            await raise_for_status(self.make_response(404, json=body))

        assert caught.value.status_code == 404
        assert caught.value.detail == body

    @pytest.mark.anyio
    async def test_the_failure_is_logged_with_the_trace_headers(self, caplog: pytest.LogCaptureFixture):
        response = self.make_response(500, json={"title": "x", "detail": "y"}, headers={"x-request-id": "r-9"})

        with caplog.at_level(logging.ERROR), pytest.raises(HTTPException):
            await raise_for_status(response)

        assert "HTTP request failed. GET http://service/thing" in caplog.text
        assert "r-9" in caplog.text

    @pytest.mark.anyio
    @pytest.mark.xfail(strict=True, raises=ValueError, reason="a non-JSON error body is not handled")
    async def test_an_error_without_a_json_body_still_becomes_an_http_exception(self):
        with pytest.raises(HTTPException) as caught:
            await raise_for_status(self.make_response(502, text="<html>Bad Gateway</html>"))

        assert caught.value.status_code == 502


class TestHttpClient:

    def test_is_unusable_before_it_is_bound(self):
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = HttpClient().client

    @pytest.mark.anyio
    async def test_binds_a_client_to_the_base_url_for_the_duration_of_the_context(self):
        http = HttpClient()

        async with http("http://service/api"):
            assert isinstance(http.client, httpx.AsyncClient)
            assert str(http.client.base_url).rstrip("/") == "http://service/api"
            bound = http.client

        assert bound.is_closed
        with pytest.raises(RuntimeError):
            _ = http.client

    @pytest.mark.anyio
    async def test_cannot_be_bound_twice_at_once(self):
        http = HttpClient()

        async with http("http://service"):
            with pytest.raises(RuntimeError, match="already bound"):
                async with http("http://other"):
                    pass

    @pytest.mark.anyio
    async def test_can_be_bound_again_after_the_context_ends(self):
        http = HttpClient()
        async with http("http://first"):
            pass

        async with http("http://second"):
            assert str(http.client.base_url).startswith("http://second")

    @pytest.mark.anyio
    async def test_is_released_when_the_body_raises(self):
        http = HttpClient()

        with pytest.raises(ValueError):
            async with http("http://service"):
                raise ValueError("boom")

        with pytest.raises(RuntimeError, match="not initialized"):
            _ = http.client

    @pytest.mark.anyio
    async def test_uses_a_thirty_second_timeout_by_default_and_honours_a_custom_one(self):
        default, custom = HttpClient(), HttpClient(timeout=5)

        async with default("http://a"), custom("http://b"):
            assert default.client.timeout.read == 30
            assert custom.client.timeout.read == 5

    @pytest.mark.anyio
    async def test_sends_the_jwt_of_the_current_request(self, monkeypatch: pytest.MonkeyPatch):
        seen = []
        install_mock_transport(monkeypatch, lambda request: seen.append(request) or httpx.Response(200, json={}))
        APP_CONTEXT.set(ContextKey.JWT, "token-7")
        http = HttpClient()

        async with http("http://service"):
            await http.client.get("/thing")

        assert seen[0].headers["Authorization"] == "Bearer token-7"

    @pytest.mark.anyio
    async def test_drops_empty_query_params_from_outgoing_requests(self, monkeypatch: pytest.MonkeyPatch):
        seen = []
        install_mock_transport(monkeypatch, lambda request: seen.append(request) or httpx.Response(200, json={}))
        http = HttpClient()

        async with http("http://service"):
            await http.client.get("/thing", params={"scope": "", "name": "pizza", "none": None})

        assert dict(seen[0].url.params) == {"name": "pizza"}

    @pytest.mark.anyio
    async def test_an_error_response_raises_an_http_exception_with_its_body(self, monkeypatch: pytest.MonkeyPatch):
        body = {"title": "Conflict", "detail": "already there"}
        install_mock_transport(monkeypatch, lambda request: httpx.Response(409, json=body))
        http = HttpClient()

        async with http("http://service"):
            with pytest.raises(HTTPException) as caught:
                await http.client.post("/thing")

        assert caught.value.status_code == 409
        assert caught.value.detail == body

    @pytest.mark.anyio
    async def test_a_successful_response_is_returned(self, monkeypatch: pytest.MonkeyPatch):
        install_mock_transport(monkeypatch, lambda request: httpx.Response(200, json={"ok": True}))
        http = HttpClient()

        async with http("http://service"):
            response = await http.client.get("/thing")

        assert response.json() == {"ok": True}

    @pytest.mark.anyio
    async def test_custom_hooks_run_first_and_are_not_modified(self, monkeypatch: pytest.MonkeyPatch):
        seen = []
        install_mock_transport(monkeypatch, lambda request: httpx.Response(200, json={}))
        APP_CONTEXT.set(ContextKey.JWT, "token-1")

        async def custom(request: httpx.Request) -> None:
            seen.append(request.headers.get("Authorization"))

        hooks = {"request": [custom]}
        http = HttpClient(hooks=hooks)

        async with http("http://service"):
            await http.client.get("/thing")

        assert seen == [None]
        assert hooks == {"request": [custom]}


class TestWithClients:

    @pytest.mark.anyio
    async def test_binds_every_client_and_releases_them_all(self):
        first, second = HttpClient(), HttpClient()

        async with with_clients((first, "http://one"), (second, "http://two")):
            assert str(first.client.base_url).startswith("http://one")
            assert str(second.client.base_url).startswith("http://two")

        for client in (first, second):
            with pytest.raises(RuntimeError):
                _ = client.client

    @pytest.mark.anyio
    async def test_releases_the_clients_already_bound_when_one_cannot_be_bound(self):
        first, second = HttpClient(), HttpClient()

        async with second("http://busy"):
            with pytest.raises(RuntimeError, match="already bound"):
                async with with_clients((first, "http://one"), (second, "http://two")):
                    pass

            with pytest.raises(RuntimeError, match="not initialized"):
                _ = first.client

    @pytest.mark.anyio
    async def test_without_clients_it_is_a_no_op(self):
        async with with_clients():
            pass


class TestResponseTransformer:

    def test_applies_the_parser_of_each_configured_field(self):
        transformer = ResponseTransformer(count=int, name=str.upper)

        assert transformer.transform({"count": "3", "name": "pizza", "other": "x"}) == {
            "count": 3, "name": "PIZZA", "other": "x",
        }

    def test_modifies_the_object_in_place(self):
        data = {"count": "3"}

        assert ResponseTransformer(count=int).transform(data) is data
        assert data == {"count": 3}

    def test_skips_missing_and_null_fields(self):
        assert ResponseTransformer(count=int).transform({"count": None}) == {"count": None}
        assert ResponseTransformer(count=int).transform({}) == {}

    def test_a_parser_error_propagates(self):
        with pytest.raises(ValueError):
            ResponseTransformer(count=int).transform({"count": "many"})

    def test_get_json_parses_the_body_then_transforms_it(self):
        response = httpx.Response(200, json={"count": "4"})

        assert ResponseTransformer(count=int).get_json(response) == {"count": 4}

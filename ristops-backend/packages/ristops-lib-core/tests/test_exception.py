import json
import logging
from http import HTTPStatus

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from helpers import make_client, make_scope
from ristops_lib_core.exception import (
    BaseHttpExceptionHandler, ErrorResponse, GenericExceptionMiddleware, GenericHttpExceptionHandler,
    RequestValidationExceptionHandler, create_error_response, get_validation_error_message,
    register_exception_handler,
)


class TestErrorResponse:

    def test_from_status_uses_the_phrase_and_the_description(self):
        error = ErrorResponse.from_status(HTTPStatus.NOT_FOUND)

        assert error.title == "Not Found"
        assert error.detail == HTTPStatus.NOT_FOUND.description

    def test_from_status_accepts_an_integer_status(self):
        assert ErrorResponse.from_status(409).title == "Conflict"

    def test_from_status_prefers_the_given_detail(self):
        assert ErrorResponse.from_status(400, "bad input").detail == "bad input"

    def test_an_unknown_status_is_rejected(self):
        with pytest.raises(ValueError):
            ErrorResponse.from_status(799)

    def test_detail_is_required_but_may_be_none(self):
        assert ErrorResponse(title="x", detail=None).detail is None
        with pytest.raises(ValidationError):
            ErrorResponse.model_validate({"title": "x"})


class TestCreateErrorResponse:

    def test_builds_the_payload_from_a_status_alone(self):
        response = create_error_response(HTTPStatus.FORBIDDEN)

        assert response.status_code == 403
        assert json.loads(response.body) == {"title": "Forbidden", "detail": HTTPStatus.FORBIDDEN.description}

    def test_builds_the_payload_from_a_detail_string(self):
        response = create_error_response(422, "bad field")

        assert json.loads(response.body) == {"title": "Unprocessable Content", "detail": "bad field"}

    def test_uses_a_ready_made_error_response_as_is(self):
        response = create_error_response(418, ErrorResponse(title="Custom", detail="teapot"))

        assert response.status_code == 418
        assert json.loads(response.body) == {"title": "Custom", "detail": "teapot"}


class TestValidationMessage:

    class Body(BaseModel):
        name: str
        age: int

    def make_error(self) -> RequestValidationError:
        try:
            self.Body.model_validate({"age": "x"})
        except ValidationError as error:
            return RequestValidationError(error.errors())
        raise AssertionError("expected a validation error")

    def test_lists_every_field_error(self):
        message = get_validation_error_message(self.make_error())

        assert message.startswith("Validation errors:")
        assert "('name',)" in message and "('age',)" in message

    def test_falls_back_when_the_errors_cannot_be_read(self, caplog: pytest.LogCaptureFixture):
        class Broken(RequestValidationError):
            def errors(self):
                raise RuntimeError("boom")

        with caplog.at_level(logging.ERROR):
            message = get_validation_error_message(Broken([]))

        assert message.endswith("failed to get error location")
        assert "Failed to parse validation error" in caplog.text


def make_request() -> Request:
    return Request(make_scope("GET", "/thing"))


class TestHandlers:

    def test_validation_handler_answers_with_422(self):
        error = TestValidationMessage().make_error()

        status, content = RequestValidationExceptionHandler()._do_handle(make_request(), error)

        assert status == HTTPStatus.UNPROCESSABLE_ENTITY
        assert content.title == HTTPStatus.UNPROCESSABLE_ENTITY.phrase
        assert "Validation errors:" in content.detail

    def test_generic_handler_wraps_a_string_detail(self):
        status, content = GenericHttpExceptionHandler()._do_handle(make_request(), HTTPException(404, "missing"))

        assert status == HTTPStatus.NOT_FOUND
        assert (content.title, content.detail) == ("Not Found", "missing")

    def test_generic_handler_passes_a_dict_detail_through(self):
        exception = HTTPException(409, {"title": "Conflict", "detail": "already there"})

        status, content = GenericHttpExceptionHandler()._do_handle(make_request(), exception)

        assert status == HTTPStatus.CONFLICT
        assert content == ErrorResponse(title="Conflict", detail="already there")

    def test_generic_handler_rejects_a_dict_that_is_not_an_error_response(self):
        with pytest.raises(ValidationError):
            GenericHttpExceptionHandler()._do_handle(make_request(), HTTPException(400, {"unexpected": True}))

    def test_handlers_declare_the_exception_they_handle(self):
        assert RequestValidationExceptionHandler().exception_cls is RequestValidationError
        assert GenericHttpExceptionHandler().exception_cls is StarletteHTTPException

    def test_the_base_handler_is_abstract(self):
        with pytest.raises(TypeError):
            BaseHttpExceptionHandler(Exception)


def build_app(*, middleware: bool = False) -> FastAPI:
    app = FastAPI()

    class Item(BaseModel):
        quantity: int

    @app.post("/items")
    async def create(item: Item) -> Item:
        return item

    @app.get("/missing")
    async def missing() -> None:
        raise HTTPException(404, "no such thing")

    @app.get("/conflict")
    async def conflict() -> None:
        raise HTTPException(409, {"title": "Conflict", "detail": "already there"})

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secret internal detail")

    register_exception_handler(app, RequestValidationExceptionHandler)
    register_exception_handler(app, GenericHttpExceptionHandler)
    if middleware:
        app.add_middleware(GenericExceptionMiddleware)
    return app


class TestRegisteredHandlers:

    @pytest.mark.anyio
    async def test_a_validation_error_becomes_a_422_error_response(self):
        async with make_client(build_app()) as client:
            response = await client.post("/items", json={"quantity": "many"})

        assert response.status_code == 422
        assert response.json()["title"] == "Unprocessable Content"
        assert "quantity" in response.json()["detail"]

    @pytest.mark.anyio
    async def test_an_http_exception_becomes_an_error_response(self):
        async with make_client(build_app()) as client:
            response = await client.get("/missing")

        assert response.status_code == 404
        assert response.json() == {"title": "Not Found", "detail": "no such thing"}

    @pytest.mark.anyio
    async def test_a_dict_detail_is_returned_as_the_body(self):
        async with make_client(build_app()) as client:
            response = await client.get("/conflict")

        assert response.status_code == 409
        assert response.json() == {"title": "Conflict", "detail": "already there"}

    @pytest.mark.anyio
    async def test_an_unknown_route_is_a_404_error_response(self):
        async with make_client(build_app()) as client:
            response = await client.get("/nowhere")

        assert response.status_code == 404
        assert response.json()["title"] == "Not Found"

    @pytest.mark.anyio
    async def test_handled_errors_are_logged(self, caplog: pytest.LogCaptureFixture):
        async with make_client(build_app()) as client:
            with caplog.at_level(logging.ERROR):
                await client.get("/missing")

        assert "Request failed: GET /missing -> 404 no such thing" in caplog.text


class TestGenericExceptionMiddleware:

    @pytest.mark.anyio
    async def test_an_unhandled_exception_becomes_a_500_without_leaking_details(self):
        async with make_client(build_app(middleware=True)) as client:
            response = await client.get("/crash")

        assert response.status_code == 500
        assert response.json()["title"] == "Internal Server Error"
        assert "secret internal detail" not in response.text

    @pytest.mark.anyio
    async def test_the_exception_is_logged(self, caplog: pytest.LogCaptureFixture):
        async with make_client(build_app(middleware=True)) as client:
            with caplog.at_level(logging.ERROR):
                await client.get("/crash")

        assert "Unexpected error: secret internal detail" in caplog.text

    @pytest.mark.anyio
    async def test_normal_responses_pass_through(self):
        async with make_client(build_app(middleware=True)) as client:
            response = await client.post("/items", json={"quantity": 3})

        assert response.status_code == 200
        assert response.json() == {"quantity": 3}

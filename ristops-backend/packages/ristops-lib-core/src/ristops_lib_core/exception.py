import abc
import logging
from abc import abstractmethod
from http import HTTPStatus
from typing import Awaitable

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

_logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """ Standard error response payload. """
    title: str = Field(title="Error title")
    detail: str | None = Field(title="Error detail")

    @classmethod
    def from_status(cls, http_status: HTTPStatus | int, detail: str = None) -> ErrorResponse:
        _http_status = http_status if isinstance(http_status, HTTPStatus) else HTTPStatus(http_status)
        return cls(
            title=_http_status.phrase,
            detail=detail or _http_status.description,
        )


def create_error_response(
        http_status: int,
        content: ErrorResponse | str | None = None,
):
    if isinstance(content, ErrorResponse):
        _content = content
    else:
        _content = ErrorResponse.from_status(http_status, content)
    return JSONResponse(
        status_code=http_status,
        content=_content.model_dump(),
    )


class BaseHttpExceptionHandler[T: Exception](abc.ABC):
    """ Exception handler to log and handle HTTP errors. """

    def __init__(self, exception_cls: type[T]) -> None:
        self._exception_cls = exception_cls

    async def __call__(self, request: Request, exception: T) -> Response | Awaitable[Response]:
        _logger.exception("Unhandled exception", exc_info=exception)
        http_status, content = self._do_handle(request, exception)
        return create_error_response(
            http_status=http_status,
            content=content,
        )

    @property
    def exception_cls(self) -> type[T]:
        return self._exception_cls

    @abstractmethod
    def _do_handle(self, request: Request, exception: T) -> tuple[int, ErrorResponse]:
        pass


def get_validation_error_message(exception: RequestValidationError) -> str:
    message = "Validation errors:"
    try:
        for error in exception.errors():
            message += f" Field: {error['loc']}, Error: {error['msg']}"
    except Exception as exc:
        _logger.exception(f"Failed to parse validation error: {exc}")
        message += " failed to get error location"
    return message


class RequestValidationExceptionHandler(BaseHttpExceptionHandler[RequestValidationError]):
    """ Exception handler to log and handle request validation errors. """

    def __init__(self) -> None:
        super().__init__(RequestValidationError)

    def _do_handle(self, request: Request, exception: RequestValidationError) -> tuple[int, ErrorResponse]:
        http_status = HTTPStatus.UNPROCESSABLE_ENTITY
        detail = get_validation_error_message(exception)
        return http_status, ErrorResponse.from_status(http_status, detail=detail)


class GenericHttpExceptionHandler(BaseHttpExceptionHandler[HTTPException]):
    """ Exception handler to log and handle generic HTTP errors. """

    def __init__(self) -> None:
        super().__init__(HTTPException)

    def _do_handle(self, request: Request, exception: HTTPException) -> tuple[int, ErrorResponse]:
        http_status = HTTPStatus(exception.status_code)
        if isinstance(exception.detail, dict):
            return http_status, ErrorResponse.model_validate(exception.detail)
        return http_status, ErrorResponse(
            title=http_status.phrase,
            detail=exception.detail,
        )


def register_exception_handler(app: FastAPI, handler_cls: type[BaseHttpExceptionHandler], *args, **kwargs):
    """ Register an exception handler to FastAPI app. """

    handler = handler_cls(*args, **kwargs)
    app.add_exception_handler(handler.exception_cls, handler)


class GenericExceptionMiddleware(BaseHTTPMiddleware):
    """ Middleware used to log exceptions and format unhandled errors. """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            _logger.exception(f"Unexpected error: {exc}")
            return create_error_response(
                http_status=HTTPStatus.INTERNAL_SERVER_ERROR,
                content=ErrorResponse.from_status(HTTPStatus.INTERNAL_SERVER_ERROR),
            )

from collections.abc import Iterator
from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute, iter_route_contexts
from starlette.routing import Match, Route
from starlette.types import Scope


def iter_api_routes(api: FastAPI) -> Iterator[tuple[APIRoute, str]]:
    """ Yield every API route with its full path, including the routes added through `include_router`.

    The full path carries the prefixes of the routers the route was included through, which `APIRoute.path` lacks.
    """
    for route_context in iter_route_contexts(api.routes):
        route, path = route_context.original_route, route_context.path
        if not isinstance(route, APIRoute):
            continue
        if path is None:
            raise RuntimeError(f"Cannot read the path of route {route.name}")
        yield route, path


def get_routes_with_attr(api: FastAPI, attr: str) -> dict[tuple[str, str], Any]:
    """ Build a set of paths+methods for routes that have attr. """
    root_path = api.root_path if api.root_path is not None else ""
    matching_routes = {}
    for route, path in iter_api_routes(api):
        if not hasattr(route.endpoint, attr):
            # skip endpoints that does not have the attribute
            continue
        value = getattr(route.endpoint, attr)
        for method in route.methods or ():
            matching_routes[(method.lower(), root_path + path)] = value
    return matching_routes


class RouteAttributeRegistry[T]:

    def __init__(self, api: FastAPI, attr: str):
        self._routes: list[tuple[Route, T]] = []
        for route, path in iter_api_routes(api):
            if not hasattr(route.endpoint, attr):
                # skip endpoints that does not have the attribute
                continue
            self._routes.append((Route(path, route.endpoint, methods=route.methods), getattr(route.endpoint, attr)))

    @property
    def has_routes(self) -> bool:
        """ Whether at least one route has the attribute. """
        return bool(self._routes)

    def get(self, scope: Scope, default: T | None = None) -> T | None:
        for route, value in self._routes:
            match, _ = route.matches(scope)
            if match == Match.FULL:
                return value
        return default

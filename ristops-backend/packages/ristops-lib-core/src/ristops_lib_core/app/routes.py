from typing import Any

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.routing import Match
from starlette.types import Scope


def get_routes_with_attr(api: FastAPI, attr: str) -> dict[tuple[str, str], Any]:
    """ Build a set of paths+methods for routes that have attr. """
    root_path = api.root_path if api.root_path is not None else ""
    matching_routes = {}
    for route in api.routes:
        if not isinstance(route, APIRoute) or not hasattr(route.endpoint, attr):
            # skip non-fastapi routes or endpoints that does not have the attribute
            continue
        value = getattr(route.endpoint, attr)
        for method in route.methods:
            matching_routes[(method.lower(), root_path + route.path)] = value
    return matching_routes


class RouteAttributeRegistry[T]:

    def __init__(self, api: FastAPI, attr: str):
        self._routes: list[tuple[APIRoute, T]] = []
        for route in api.routes:
            if not isinstance(route, APIRoute) or not hasattr(route.endpoint, attr):
                # skip non-fastapi routes or endpoints that does not have the attribute
                continue
            value = getattr(route.endpoint, attr)
            self._routes.append((route, value))

    def get(self, scope: Scope, default: T = None) -> T:
        for route, value in self._routes:
            match, _ = route.matches(scope)
            if match == Match.FULL:
                return value
        return default

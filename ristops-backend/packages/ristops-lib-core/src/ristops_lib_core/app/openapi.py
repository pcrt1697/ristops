from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from ristops_lib_core.app.routes import get_routes_with_attr
from ristops_lib_core.auth.authn import IS_PUBLIC


class OpenAPIConfiguration:

    def __init__(self, app: FastAPI, bearer_auth: bool = False):
        self._app = app
        self._bearer_auth = bearer_auth

    def __call__(self):
        if self._app.openapi_schema:
            return self._app.openapi_schema

        schema = get_openapi(
            title=self._app.title,
            version=self._app.version,
            routes=self._app.routes,
        )

        if self._bearer_auth:
            schema["components"]["securitySchemes"] = {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
        public_routes = get_routes_with_attr(self._app, IS_PUBLIC)

        # apply security only to non-public endpoints
        for path, path_item in schema.get("paths", {}).items():
            for method, operation in path_item.items():
                if (method, self._app.root_path + path) not in public_routes:
                    operation["security"] = [{"BearerAuth": []}]
                else:
                    operation["security"] = []  # explicitly empty = no lock

        return schema

"""HTTP tools: the JSON schema of a tool's arguments, built from the OpenAPI operation it calls."""

from typing import Any

_OPENAPI_REF_PREFIX = "#/components/schemas/"
_DEFS_REF_PREFIX = "#/$defs/"
_BODY_ARGUMENT = "body"


def _rewrite_refs(node: Any) -> Any:
    """Return a copy of the schema with OpenAPI component references turned into `$defs` references.

    The OpenAPI-only `discriminator` keyword is dropped: it is not JSON Schema and its mapping holds references that
    would not resolve.
    """
    if isinstance(node, dict):
        return {
            key: value.replace(_OPENAPI_REF_PREFIX, _DEFS_REF_PREFIX)
            if key == "$ref" and isinstance(value, str) else _rewrite_refs(value)
            for key, value in node.items()
            if key != "discriminator"
        }
    if isinstance(node, list):
        return [_rewrite_refs(item) for item in node]
    return node


def _collect_defs(node: Any, components: dict[str, Any], found: dict[str, Any]) -> None:
    """Collect into `found` the components that the schema references, directly or through other components."""
    if isinstance(node, dict):
        reference = node.get("$ref")
        if isinstance(reference, str) and reference.startswith(_DEFS_REF_PREFIX):
            name = reference.removeprefix(_DEFS_REF_PREFIX)
            if name not in found:
                found[name] = _rewrite_refs(components[name])
                _collect_defs(found[name], components, found)
        for value in node.values():
            _collect_defs(value, components, found)
    elif isinstance(node, list):
        for item in node:
            _collect_defs(item, components, found)


def _build_input_schema(operation: dict[str, Any], components: dict[str, Any]) -> dict[str, Any]:
    """Build the JSON schema of a tool's arguments from an OpenAPI operation.

    Path and query parameters become top-level properties under their own names. The JSON request body, if any,
    becomes a single property named `body`, which keeps discriminated bodies intact and avoids name collisions.
    """
    properties: dict[str, Any] = {}
    required: list[str] = []
    for parameter in operation.get("parameters", []):
        if parameter["in"] not in ("path", "query"):
            continue
        if parameter["name"] == _BODY_ARGUMENT:
            raise ValueError(f"A parameter named `{_BODY_ARGUMENT}` collides with the request body argument")
        schema = dict(parameter.get("schema", {}))
        if description := parameter.get("description"):
            schema.setdefault("description", description)
        properties[parameter["name"]] = schema
        if parameter.get("required"):
            required.append(parameter["name"])

    request_body = operation.get("requestBody", {})
    body_schema = request_body.get("content", {}).get("application/json", {}).get("schema")
    if body_schema is not None:
        properties[_BODY_ARGUMENT] = body_schema
        if request_body.get("required"):
            required.append(_BODY_ARGUMENT)

    input_schema: dict[str, Any] = _rewrite_refs({"type": "object", "properties": properties})
    if required:
        input_schema["required"] = required
    definitions: dict[str, Any] = {}
    _collect_defs(input_schema, components, definitions)
    if definitions:
        input_schema["$defs"] = definitions
    return input_schema

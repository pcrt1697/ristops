import logging
from http import HTTPStatus

from fastapi import HTTPException
from neo4j import Record
from redis.typing import EncodableT

from ristops_be_authz.database.engine import get_neo4j_transaction
from ristops_be_authz.domain.models import ResourceNode
from ristops_lib_core.schema.authz import ResourceType, CreateAuthorizationResourceRequest, AuthorizationResource

_logger = logging.getLogger(__name__)


def make_resource_id(resource_type: str, resource_id: str) -> str:
    """ Creates a unique resource id for the given resource type and resource id. """
    return f"{resource_type}~{resource_id}"


async def find_resource_or_throw(resource_type: str, resource_id: str) -> ResourceNode:
    record = await _find_resource(resource_type, resource_id)
    if record is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Resource not found")
    return ResourceNode.model_validate(record["r"])


async def find_or_create_user_resource(user_id: str) -> None:
    _logger.info("Creating user resource for %s", user_id)
    resources = [
        AuthorizationResource(
            resource_id=user_id,
            resource_type=ResourceType.USER,
        )
    ]
    request = CreateAuthorizationResourceRequest(resources=resources)
    await find_or_create_resources(
        parent_type=ResourceType.APP,
        parent_id="*",
        request=request,
    )


async def find_or_create_resources(
        parent_type: ResourceType,
        parent_id: str,
        request: CreateAuthorizationResourceRequest
) -> list[ResourceNode]:
    _logger.info("Creating %s resources", len(request.resources))
    parent = await find_resource_or_throw(parent_type, parent_id)
    transaction = get_neo4j_transaction()
    nodes = []
    # todo: maybe optimize this with a single query
    for resource in request.resources:
        _id = make_resource_id(resource.resource_type, resource.resource_id)
        result = await transaction.run(
            """
            MATCH (p:Resource {id: $parent_id})
            MERGE (c:Resource {id: $child_id})
            ON CREATE SET c.resource_id = $resource_id, c.resource_type = $resource_type
            MERGE (c)-[:BELONGS_TO]->(p)
            RETURN c
            ;
            """,
            parent_id=parent.id,
            child_id=_id,
            resource_id=resource.resource_id,
            resource_type=resource.resource_type,
        )
        record = await result.single()
        assert record is not None, "Failed to create resource"
        node = ResourceNode.model_validate(record["c"])
        _logger.info("Created resource %s", node.id)
        nodes.append(node)
    return nodes


async def find_or_create_root() -> ResourceNode:
    return await _find_or_create_resource(ResourceType.APP.value, "*")


async def _find_or_create_resource(
        resource_type: str,
        resource_id: str,
) -> ResourceNode:
    _id = make_resource_id(resource_type, resource_id)
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        """
        MERGE (r:Resource {id: $id})
        ON CREATE SET r.resource_id = $resource_id, r.resource_type = $resource_type
        RETURN r
        """,
        id=_id,
        resource_id=resource_id,
        resource_type=resource_type,
    )
    record = await result.single()
    assert record is not None, "Failed to get or create resource"
    node = ResourceNode.model_validate(record["r"])
    _logger.info("Created resource %s", node.id)
    return node


async def _find_resource(
        resource_type: str,
        resource_id: str,
) -> Record | None:
    _id = make_resource_id(resource_type, resource_id)
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        """
        MATCH (r:Resource {id: $id})
        RETURN r
        LIMIT 1
        """,
        id=_id,
    )
    return await result.single()


async def resource_exists(resource_type: str, resource_id: str) -> bool:
    record = await _find_resource(resource_type, resource_id)
    return record is not None


async def throw_if_resource_not_exists(resource_type: str, resource_id: str) -> None:
    _resource_exists = await resource_exists(resource_type, resource_id)
    if not _resource_exists:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Resource not found")


async def delete_resource(resource_type: str, resource_id: str) -> None:
    transaction = get_neo4j_transaction()
    _id = make_resource_id(resource_type, resource_id)
    await transaction.run(
        """
        MATCH (r:Resource {id: $id})
        DETACH DELETE r
        """,
        id=_id,
    )
    _logger.info(f"Deleted resource {_id}")


async def on_resource_event(stream_id: str, payload: EncodableT) -> None:
    pass

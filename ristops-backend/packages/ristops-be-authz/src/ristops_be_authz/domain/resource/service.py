import logging
from http import HTTPStatus

from fastapi import HTTPException
from neo4j import Record

from ristops_be_authz.domain.models import ResourceNode
from ristops_lib_be.authz.events import (
    resource_lifecycle_event_adapter, ResourceCreatedLifecycleEvent,
    ResourceDeletedLifecycleEvent
)
from ristops_lib_be.events import LifecycleOperationType
from ristops_lib_core.schema.authz import ResourceType, AuthorizationResource
from ristops_lib_neo4j.engine import get_neo4j_transaction, neo4j_transaction_provider
from ristops_lib_redis.engine import StreamPayload

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
    await find_or_create_resources(
        parent_type=ResourceType.APP,
        parent_id="*",
        resources=resources,
    )


async def find_or_create_resources(
        parent_type: ResourceType,
        parent_id: str,
        resources: list[AuthorizationResource],
) -> list[ResourceNode]:
    _logger.info("Creating %s resources", len(resources))
    parent = await find_resource_or_throw(parent_type, parent_id)
    transaction = get_neo4j_transaction()
    nodes = []
    # todo: maybe optimize this with a single query
    for resource in resources:
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
        if record is None:
            raise RuntimeError("Failed to create resource")
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
    if record is None:
        raise RuntimeError("Failed to get or create resource")
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


async def delete_resource(resource_type: ResourceType, resource_id: str) -> None:
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


async def on_resource_event(_: str, payload: StreamPayload) -> None:
    event = resource_lifecycle_event_adapter.validate_json(payload)
    async with neo4j_transaction_provider.context():
        if event.operation == LifecycleOperationType.CREATED:
            _event: ResourceCreatedLifecycleEvent = event
            await find_or_create_resources(_event.parent_type, _event.parent_id, _event.resources)
        elif event.operation == LifecycleOperationType.DELETED:
            _event: ResourceDeletedLifecycleEvent = event
            await delete_resource(_event.resource_type, _event.resource_id)

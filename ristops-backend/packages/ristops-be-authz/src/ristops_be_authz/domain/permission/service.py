from ristops_lib_neo4j.engine import get_neo4j_transaction


async def list_permissions(query: str | None) -> list[str]:
    """List permissions using `contains` operator"""
    _query = query.lower() if query else None
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        """MATCH (p:Permission)
        WHERE $query IS NULL OR toLower(p.id) CONTAINS $query
        RETURN p.id AS id
        """,
        query=_query,
    )
    return [record["id"] async for record in result]

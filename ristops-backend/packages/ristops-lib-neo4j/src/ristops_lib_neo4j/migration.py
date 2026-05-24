import logging
import re
from datetime import datetime, UTC
from enum import StrEnum
from importlib.resources.abc import Traversable
from typing import TypedDict, LiteralString, cast

from pydantic import BaseModel, Field

from ristops_lib_neo4j.engine import get_neo4j_transaction, AsyncNeo4jTransactionProvider

_logger = logging.getLogger(__name__)


class MigrationType(StrEnum):
    SCHEMA = "schema"
    DATA = "data"


class MigrationNode(BaseModel):
    __label__ = "Migration"

    id: int = Field(description="ID of migration (aka the migration version)")
    name: str = Field(description="Name of migration")
    type: MigrationType = Field(description="Type of migration")
    applied_at: str = Field(description="Migration run date")


class MigrationInfo(TypedDict):
    id: int
    type: MigrationType
    name: str
    file: Traversable


def _get_migration_info(file: Traversable) -> MigrationInfo:
    match = re.match(r"([0-9]+)\.(schema|data)\.(.+)\.cypher", file.name)
    if match is None or len(match.groups()) != 3:
        raise ValueError(f"Found invalid migration filename: {file.name}")
    _id, type_name, name = match.groups()
    _type = MigrationType(type_name)
    return {
        "id": int(_id),
        "type": _type,
        "name": name,
        "file": file,
    }


def _get_migrations(last_migration: int, migrations_dir: Traversable) -> dict[int, MigrationInfo]:
    migrations: dict[int, MigrationInfo] = {}
    for file in migrations_dir.iterdir():
        if not file.is_file() or not file.name.endswith(".cypher"):
            continue
        migration_info = _get_migration_info(file)
        if migration_info is None:
            continue
        if migration_info["id"] <= last_migration:
            continue
        migrations[migration_info["id"]] = migration_info
    return migrations


async def get_last_migration() -> int:
    transaction = get_neo4j_transaction()
    result = await transaction.run(
        """
        MATCH (m:Migration)
        RETURN m
        ORDER BY m.id DESC
        LIMIT 1
        """
    )
    record = await result.single()
    if record is None:
        return -1
    return record["m"].get("id", -1)


def _parse_migration_script(file: Traversable) -> list[str]:
    script = file.read_text()
    queries = []
    current_query = []
    for text in script.split("\n"):
        _text = text.strip()
        if _text.startswith("//") or not _text:
            continue
        current_query.append(_text)
        if _text.endswith(";"):
            queries.append(" ".join(current_query))
            current_query = []
    return queries


async def _run_migration(migration: MigrationInfo) -> None:
    _extra = {
        "migration_id": migration["id"],
        "migration_type": migration["type"],
        "migration_name": migration["name"],
        "migration_file": migration["file"],
    }
    _logger.info("Parsing migration", extra=_extra)

    queries = _parse_migration_script(migration["file"])
    _logger.info("Found %s queries in migration file", len(queries), extra=_extra)

    transaction = get_neo4j_transaction()
    for query in queries:
        _logger.info("Running migration query %s", query, extra=_extra)
        _query = cast(LiteralString, query)
        await transaction.run(_query)
    _logger.info("Successfully executed %s queries", len(queries), extra=_extra)


async def _save_migration(migration: MigrationInfo) -> None:
    _id = migration["id"]
    _logger.info(
        "Saving migration...",
        extra={
            "migration_version": _id,
            "migration_type": migration["type"],
            "migration_name": migration["name"],
        }
    )
    transaction = get_neo4j_transaction()
    _applied_at = datetime.now(UTC).isoformat()
    if _id == 0:
        result = await transaction.run(
            """
            CREATE (m:Migration {
                id: $id,
                name: $name,
                type: $type,
                applied_at: $applied_at
            })
            RETURN m
            """,
            id=_id,
            name=migration["name"],
            type=migration["type"],
            applied_at=_applied_at,
        )
    else:
        result = await transaction.run(
            """
            MATCH (prev:Migration {id: $prev_id})
            CREATE (m:Migration {
                id: $id,
                name: $name,
                type: $type,
                applied_at: $applied_at
            })
            CREATE (prev)-[:NEXT]->(m)
            RETURN m
            """,
            id=_id,
            name=migration["name"],
            type=migration["type"],
            applied_at=_applied_at,
            prev_id=migration["id"] - 1,
        )
    record = await result.single()
    if record is None:
        raise RuntimeError("Migration creation returned no record")
    _migration = MigrationNode.model_validate(record["m"])
    _logger.info("Created migration %s", _migration.id)


async def _run_migrations(
        transaction_provider: AsyncNeo4jTransactionProvider,
        migrations: dict[int, MigrationInfo],
) -> None:
    ids = sorted(migrations.keys())
    for migration_id in ids:
        migration = migrations[migration_id]
        async with transaction_provider.context():
            await _run_migration(migrations[migration_id])
        async with transaction_provider.context():
            await _save_migration(migration)


async def run_migrations(
        transaction_provider: AsyncNeo4jTransactionProvider,
        migrations_dir: Traversable,
) -> None:
    """Run all pending migrations from ``migrations_dir``.

    ``migrations_dir`` is a ``Traversable`` pointing at the directory that
    contains the ``.cypher`` migration files — typically obtained via
    ``importlib.resources.files("your.package").joinpath("migrations")``.
    """
    _logger.info("Starting database migration")
    async with transaction_provider.context():
        last_migration = await get_last_migration()
    _logger.info("The last migration id is %s", last_migration)

    migrations = _get_migrations(last_migration, migrations_dir)
    _logger.info("Found %s migrations to run", len(migrations))

    if len(migrations) > 0:
        await _run_migrations(transaction_provider, migrations)
    else:
        _logger.info("No migrations to run")

import importlib
import logging

import click
from sqlalchemy import MetaData, Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.ddl import CreateIndex, CreateSchema, CreateTable

from ristops_lib_core.cli.utils.command import async_command
from ristops_lib_core.cli.utils.entrypoints import load_command_entrypoint, get_command_group_entrypoint_names
from ristops_lib_sql.engine import sql_session_provider, with_sql_db

_GROUP_SUFFIX = "sql_database.generate_ddl"
_AVAILABLE_APPS = get_command_group_entrypoint_names(suffix=_GROUP_SUFFIX)


def _load_models(app: str) -> tuple[type[DeclarativeBase], ...]:
    """Load the ``MODELS`` tuple registered by ``app`` under the generate_ddl group."""
    _logger = logging.getLogger(__name__)
    entities_path = load_command_entrypoint(app, _GROUP_SUFFIX)
    try:
        package_path, tuple_name = entities_path.split(":")
        module = importlib.import_module(package_path)
        return getattr(module, tuple_name)
    except Exception as e:
        _logger.exception(f"Failed to load object {entities_path}")
        raise e


@click.group(
    context_settings=dict(
        # avoid truncation of help text
        max_content_width=130,
    ),
)
@click.pass_context
def sql_database(_: click.Context) -> None:
    """ Database related commands. """
    pass


@click.command(
    help="Generate SQL DDL statements for the service entities."
)
@click.argument(
    "app",
    type=click.Choice(_AVAILABLE_APPS),
    required=True,
)
def generate_ddl(app: str) -> None:
    """
    Requires entrypoint group sql_database.generate_ddl to define the 'models' value, which is a path
    (using the format <package>.<path>:<tuple>) that points to a tuple object that contains all entity classes.
    """
    _logger = logging.getLogger(__name__)
    tuple_obj = _load_models(app)

    ddl = []
    for table_cls in tuple_obj:
        # noinspection PyTypeChecker
        table: Table = table_cls.__table__
        if not isinstance(table, Table):
            raise ValueError(f"Invalid model class {table_cls}")
        _stmt = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        stmt = "\n".join([item.rstrip().replace("\t", "  ") for item in _stmt.strip("\n").split("\n")])
        indexes = []
        for index in table.indexes:
            index_stmt = str(CreateIndex(index).compile(dialect=postgresql.dialect()))
            indexes.append(index_stmt.strip("\n"))
        if indexes:
            stmt = ";\n".join([stmt] + indexes)
        ddl.append(stmt)

    _logger.info("Generated SQL statements: \n" + ";\n\n".join(ddl).lower() + ";")


@click.command(
    help="Drop and recreate all tables for the service from its models. DESTRUCTIVE: all data is lost.",
)
@click.argument(
    "app",
    type=click.Choice(_AVAILABLE_APPS),
    required=True,
)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    help="Skip the confirmation prompt.",
)
@click.pass_context
@async_command
@with_sql_db
async def nuke(_: click.Context, app: str, force: bool) -> None:
    """
    Drop and recreate every table declared by the service's ``MODELS`` tuple.

    Reuses the same entrypoint as ``generate-ddl``. Connects to the database
    resolved from the current environment, so run it in the target service's
    environment (``.env`` / ``RISTOPS_ENV_PATH``).
    """
    _logger = logging.getLogger(__name__)
    metadata: MetaData = _load_models(app)[0].metadata

    if not force:
        click.confirm(
            f"This will DROP and recreate all tables for '{app}'. All data will be lost. Continue?",
            abort=True,
        )

    async with sql_session_provider.context() as session:
        connection = await session.connection()
        await connection.run_sync(metadata.drop_all)
        await connection.run_sync(metadata.create_all)

    _logger.info("Schema for '%s' has been reset.", app)


@click.command(
    help="Create any tables missing for the service from its models. Idempotent and non-destructive.",
)
@click.argument(
    "app",
    type=click.Choice(_AVAILABLE_APPS),
    required=True,
)
@click.pass_context
@async_command
@with_sql_db
async def create_tables(_: click.Context, app: str) -> None:
    """
    Create the service's schema and any tables declared by its ``MODELS`` tuple that
    do not exist yet.

    Unlike ``nuke`` this never drops anything, and unlike ``generate-ddl`` it applies
    the DDL instead of printing it, so it is safe to run on every startup. Reuses the
    same entrypoint as the other commands and connects to the database resolved from
    the current environment (``.env`` / ``RISTOPS_ENV_PATH``).
    """
    _logger = logging.getLogger(__name__)
    metadata: MetaData = _load_models(app)[0].metadata

    # entities bind their schema per-table via make_table_args(), not on the metadata
    schemas = {table.schema for table in metadata.tables.values() if table.schema}

    async with sql_session_provider.context() as session:
        connection = await session.connection()
        for schema in sorted(schemas):
            await connection.execute(CreateSchema(schema, if_not_exists=True))
        await connection.run_sync(metadata.create_all, checkfirst=True)

    _logger.info("Schema for '%s' is up to date.", app)


# noinspection PyTypeChecker
sql_database.add_command(generate_ddl)
# noinspection PyTypeChecker
sql_database.add_command(create_tables)
# noinspection PyTypeChecker
sql_database.add_command(nuke)

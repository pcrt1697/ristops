import importlib
import logging

import click
from sqlalchemy import Table
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.ddl import CreateTable, CreateIndex

from ristops_lib_core.cli.utils.entrypoints import load_command_entrypoint, get_command_group_entrypoint_names

_GROUP_SUFFIX = "sql_database.generate_ddl"
_AVAILABLE_APPS = get_command_group_entrypoint_names(suffix=_GROUP_SUFFIX)


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
    entities_path = load_command_entrypoint(app, _GROUP_SUFFIX)
    try:
        package_path, tuple_name = entities_path.split(":")
        module = importlib.import_module(package_path)
        tuple_obj: tuple[DeclarativeBase] = getattr(module, tuple_name)
    except Exception as e:
        _logger.exception(f"Failed to load object {entities_path}")
        raise e

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


# noinspection PyTypeChecker
sql_database.add_command(generate_ddl)

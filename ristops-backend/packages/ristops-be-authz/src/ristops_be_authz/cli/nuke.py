import logging

import click

from ristops_lib_core.cli.utils.command import async_command
from ristops_lib_neo4j.engine import with_neo4j_db, neo4j_transaction_provider

_logger = logging.getLogger(__name__)


@click.command(
    help="Delete all authz Neo4j nodes and relationships. DESTRUCTIVE: run seed-authz to rebuild.",
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
@with_neo4j_db
async def nuke(_: click.Context, force: bool) -> None:
    """
    Delete every node and relationship from the authz graph.

    Constraints and indexes are left in place (the schema migration is
    idempotent); the ``Migration`` nodes are removed, so ``seed-authz`` re-runs
    all migrations from scratch and recreates the admin ACL.
    """
    if not force:
        click.confirm(
            "This will DELETE ALL nodes and relationships in the authz Neo4j database. Continue?",
            abort=True,
        )

    async with neo4j_transaction_provider.context() as transaction:
        await transaction.run("MATCH (n) DETACH DELETE n")

    _logger.info("All authz nodes have been deleted. Run 'seed-authz' to rebuild.")

import logging

import click

from ristops_be_authz.database.engine import neo4j_transaction_provider
from ristops_be_authz.database.migration import run_migrations
from ristops_be_authz.domain.acl.service import setup_admin_acl
from ristops_lib_core.cli.utils.command import async_command

_logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@async_command
async def seed(_: click.Context):
    """ Seed app by running migrations and creating the admin ACL. """

    await neo4j_transaction_provider.configure()
    try:
        await run_migrations(neo4j_transaction_provider)
        async with neo4j_transaction_provider.context():
            await setup_admin_acl()
    finally:
        await neo4j_transaction_provider.close()

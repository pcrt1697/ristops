import logging

import click

from ristops_be_authz.database.engine import neo4j_transaction_provider, with_neo4j_db
from ristops_be_authz.database.migration import run_migrations
from ristops_be_authz.domain.acl.service import setup_admin_acl
from ristops_lib_core.cli.utils.command import async_command

_logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@async_command
@with_neo4j_db
async def seed(_: click.Context):
    """ Seed app by running migrations and creating the admin ACL. """
    await run_migrations(neo4j_transaction_provider)
    await setup_admin_acl()

import logging

import click

from ristops_be_authz.database.migration import migrate
from ristops_be_authz.domain.acl.service import setup_admin_acl
from ristops_lib_core.cli.utils.command import async_command
from ristops_lib_neo4j.engine import with_neo4j_db

_logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@async_command
@with_neo4j_db
async def seed(_: click.Context):
    """ Seed app by running migrations and creating the admin ACL. """
    await migrate()
    await setup_admin_acl()

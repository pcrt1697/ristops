import logging

import click

from ristops_be_authz.database.migration import migrate
from ristops_be_authz.domain.acl.service import initialize_acl_seed, assign_admin_role
from ristops_be_authz.domain.user.service import upsert_user
from ristops_lib_core.cli.utils.command import async_command
from ristops_lib_core.schema.user import AppMember
from ristops_lib_neo4j.engine import with_neo4j_db, neo4j_transaction_provider

_logger = logging.getLogger(__name__)


@click.command()
@click.pass_context
@async_command
@with_neo4j_db
async def seed(_: click.Context):
    """ Seed app by running migrations and creating the admin ACL. """
    await migrate()
    async with neo4j_transaction_provider.context():
        admin_id = await initialize_acl_seed()

        member_info = AppMember(
            id=admin_id,
            username=str(admin_id),
        )
        await upsert_user(member_info)

        await assign_admin_role(admin_id)

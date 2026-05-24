import logging

import click

from ristops_be_authn.domain.user.service import create_or_update_admin
from ristops_lib_core.auth.authn import DEFAULT_ADMIN_USERNAME
from ristops_lib_core.cli.utils.command import async_command
from ristops_lib_core.settings import ENVVARS_PREFIX
from ristops_lib_redis.engine import redis_client
from ristops_lib_sql.engine import sql_session_provider

_logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "-u",
    "--username",
    type=str,
    default=DEFAULT_ADMIN_USERNAME,
    help="Admin username.",
)
@click.option(
    "-e",
    "--email",
    type=str,
    default="admin@ristops.com",
    help="Admin email address.",
)
@click.option(
    "-p",
    "--password",
    type=str,
    help="Admin password.",
    envvar=ENVVARS_PREFIX + "ADMIN_PWD",
)
@click.pass_context
@async_command
async def seed(_: click.Context, username: str, email: str, password: str):
    """ Seed app by creating the admin user. """
    from ristops_be_authn.services.http import get_http_clients, http_service
    clients = get_http_clients()
    await redis_client.connect()
    try:
        async with http_service(clients):
            await sql_session_provider.configure()
            async with sql_session_provider.context():
                _logger.info(f"Setting up admin user")
                await create_or_update_admin(
                    username=username,
                    display_name=email,
                    email=email,
                    password=password,
                )
    except Exception as exc:
        _logger.exception(exc)
    finally:
        await redis_client.disconnect()

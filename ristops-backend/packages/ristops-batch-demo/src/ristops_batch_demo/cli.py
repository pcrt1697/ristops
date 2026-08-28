import logging
from pathlib import Path

import click

from ristops_lib_core.cli.utils.command import async_command
from ristops_lib_core.settings import ENVVARS_PREFIX

_logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def demo(_: click.Context):
    """ RistOps demo commands. """
    pass


@click.command(help="Seed demo users, venues, and role assignments through the backend APIs.")
@click.option(
    "-u",
    "--users",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the users JSON file.",
)
@click.option(
    "-v",
    "--venues",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the venues JSON file.",
)
@click.option(
    "-s",
    "--services",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the services JSON file.",
)
@click.option(
    "-a",
    "--assignments",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the role assignments JSON file.",
)
@click.option(
    "-e",
    "--admin-email",
    type=str,
    default="admin@ristops.com",
    help="Admin email used to authenticate.",
)
@click.option(
    "-p",
    "--admin-password",
    type=str,
    required=True,
    envvar=ENVVARS_PREFIX + "ADMIN_PWD",
    help="Admin password used to authenticate.",
)
@click.pass_context
@async_command
async def seed(
        _: click.Context,
        users: Path,
        venues: Path,
        services: Path,
        assignments: Path,
        admin_email: str,
        admin_password: str,
) -> None:
    """ Seed demo data by calling the authn, venue, reservation, and authz REST APIs. """
    from ristops_batch_demo.seed.models import (
        DemoAssignments, DemoServices, DemoUsers, DemoVenues,
    )
    from ristops_batch_demo.seed.seeder import DemoSeeder
    from ristops_batch_demo.services.http import (
        authn_client, authz_client, reservation_client, venue_client,
    )
    from ristops_batch_demo.settings import BackendServiceSettings
    from ristops_lib_core.http import with_clients

    demo_users = DemoUsers.model_validate_json(users.read_text())
    demo_venues = DemoVenues.model_validate_json(venues.read_text())
    demo_services = DemoServices.model_validate_json(services.read_text())
    demo_assignments = DemoAssignments.model_validate_json(assignments.read_text())

    be_settings = BackendServiceSettings.get()
    seeder = DemoSeeder(
        users=demo_users,
        venues=demo_venues,
        services=demo_services,
        assignments=demo_assignments,
        admin_email=admin_email,
        admin_password=admin_password,
    )
    try:
        async with with_clients(
                (authn_client, be_settings.authn_url),
                (venue_client, be_settings.venue_url),
                (reservation_client, be_settings.reservation_url),
                (authz_client, be_settings.authz_url),
        ):
            await seeder.run()
    except Exception as exc:
        _logger.exception(exc)
        raise


demo.add_command(seed)

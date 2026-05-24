import click
import uvicorn

from ristops_lib_core.cli.utils.entrypoints import load_command_entrypoint_object, get_command_group_entrypoint_names
from ristops_lib_core.logging import uvicorn_logging_config
from ristops_lib_core.settings import ENVVARS_PREFIX

_GROUP_SUFFIX = "start"
_AVAILABLE_APPS = get_command_group_entrypoint_names(suffix=_GROUP_SUFFIX)


@click.command(
    help="Start FastAPI app.",
)
@click.argument(
    "app",
    type=click.Choice(_AVAILABLE_APPS),
    required=True,
)
@click.option(
    "-p",
    "--port",
    type=int,
    default=8000,
    help="Port used to expose the APIs.",
    envvar=ENVVARS_PREFIX + "PORT",
)
@click.pass_context
def start(_: click.Context, app: str, port: int):
    """
    Start FastAPI app.

    :param _: Click context.
    :param app: FastAPI app name as defined in pyproject.toml under the entrypoint group `ristops.cli.commands.start`
        where the entrypoint name is the app name passed to the command as positional argument,
        and the value is the path to the factory function.
    :param port: Port used to expose the APIs.
    """

    app_factory = load_command_entrypoint_object(name=app, suffix=_GROUP_SUFFIX)
    app = app_factory()
    uvicorn.run(
        app,
        host='0.0.0.0',
        port=port,
        root_path='',
        log_config=uvicorn_logging_config()
    )

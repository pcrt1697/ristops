import json
import pathlib

import click
from fastapi import FastAPI

from ristops_lib_core.cli.utils.entrypoints import load_command_entrypoint_object, get_command_group_entrypoint_names

_GROUP_SUFFIX = "openapi.export"
_AVAILABLE_APPS = get_command_group_entrypoint_names(suffix=_GROUP_SUFFIX)


@click.group(
    context_settings=dict(
        # avoid truncation of help text
        max_content_width=130,
    ),
)
@click.pass_context
def openapi(_: click.Context) -> None:
    """ OpenAPI related commands. """
    pass


@click.command(
    help="Export the OpenAPI schema of an app as JSON. Writes to a file if --file is provided, otherwise prints to "
         "stdout.",
)
@click.argument(
    "app",
    type=click.Choice(_AVAILABLE_APPS),
    required=True,
)
@click.option(
    "-f",
    "--file",
    type=click.Path(),
    default=None,
    help="Output file path. Defaults to stdout.",
)
@click.option(
    "-o",
    "--overwrite",
    is_flag=True,
    default=False,
    help="Overwrite the output file if it already exists.",
)
def export(app: str, file: str | None, overwrite: bool) -> None:
    """
    Export the OpenAPI schema of an app.

    :param app: App name as defined in pyproject.toml under the entrypoint group `ristops.cli.commands.openapi.export`,
        whose value is the path to a factory that builds the API without settings, telemetry or I/O.
    :param file: Output file path, stdout when omitted.
    :param overwrite: Whether to replace an existing output file.
    """
    api_factory = load_command_entrypoint_object(name=app, suffix=_GROUP_SUFFIX)
    api: FastAPI = api_factory()
    # key order is kept as FastAPI emits it (route and field declaration order), which is already deterministic
    content = json.dumps(api.openapi(), indent=2, ensure_ascii=False) + "\n"
    if file:
        out = pathlib.Path(file)
        if out.exists() and not overwrite:
            raise click.UsageError(f"File already exists: {out}. Use --overwrite to replace it.")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content)
    else:
        click.echo(content, nl=False)


# noinspection PyTypeChecker
openapi.add_command(export)

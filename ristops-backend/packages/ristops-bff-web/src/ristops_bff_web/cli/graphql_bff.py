import pathlib

import click
from strawberry.printer import print_schema

from ristops_bff_web.graphql.schema import schema


@click.group(
    context_settings=dict(
        max_content_width=130,
    ),
)
@click.pass_context
def graphql_bff(_: click.Context) -> None:
    """GraphQL BFF related commands."""
    pass


@click.command(
    help="Export the BFF GraphQL schema as SDL. Writes to a file if --file is provided, otherwise prints to stdout.",
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
def export_schema(file: str | None, overwrite: bool) -> None:
    """Export the BFF GraphQL schema as SDL."""
    sdl = print_schema(schema) + "\n"
    if file:
        out = pathlib.Path(file)
        if out.exists() and not overwrite:
            raise click.UsageError(f"File already exists: {out}. Use --overwrite to replace it.")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(sdl)
    else:
        click.echo(sdl, nl=False)


# noinspection PyTypeChecker
graphql_bff.add_command(export_schema)

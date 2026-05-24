from pathlib import Path

import click


@click.group()
@click.pass_context
async def demo(_: click.Context):
    """ RistOps demo commands. """
    pass


@click.command(
    help="Seed demo data."
)
@click.option(
    "-d",
    "--data",
    type=click.Path(exists=True),
    required=True,
)
def seed(data: Path) -> None:
    pass

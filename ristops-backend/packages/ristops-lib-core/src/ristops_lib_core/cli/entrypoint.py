import click

from ristops_lib_core.cli.utils.command import MainGroup
from ristops_lib_core.logging import configure_logging


@click.group(
    name='ristops',
    cls=MainGroup,
    help="RistOps command line interface",
    context_settings=dict(
        # avoid truncation of help text
        max_content_width=130,
    ),
)
@click.pass_context
def main(ctx: click.Context) -> None:
    ctx.ensure_object(dict)
    configure_logging()

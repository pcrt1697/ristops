import asyncio
import functools
from importlib.metadata import entry_points

import click

from ristops_lib_core.utils import load_object

ENTRYPOINT_COMMANDS_GROUP_NAME = "ristops.cli.commands"


def get_command_path(ctx: click.Context, cmd_name: str) -> str:
    commands = ctx.command_path.split()[1:]
    commands.append(cmd_name)
    return ".".join(commands).replace("_", "-")


class MainGroup(click.Group):
    def __init__(
            self,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        # <command-name> -> package.path:<object-name>
        self._commands = {
            entrypoint.name: entrypoint.value
            for entrypoint in entry_points(group=ENTRYPOINT_COMMANDS_GROUP_NAME)
        }

    def list_commands(self, ctx: click.Context) -> list[str]:
        base = super().list_commands(ctx)
        lazy = sorted(self._commands.keys())
        return base + lazy

    def get_command(self, ctx, cmd_name: str) -> click.Command | None:
        cmd_path = get_command_path(ctx, cmd_name)
        if cmd_path in self._commands:
            return self._lazy_load(cmd_path)
        return super().get_command(ctx, cmd_name)

    def _lazy_load(self, cmd_path: str) -> click.Command:
        import_path = self._commands[cmd_path]
        cmd_object: click.Command = load_object(import_path)
        if not isinstance(cmd_object, click.Command):
            raise ValueError(f"Lazy loading of {cmd_path} -> {import_path} failed by returning a non-command object")
        cmd_object.name = cmd_path
        return cmd_object


def async_command(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper

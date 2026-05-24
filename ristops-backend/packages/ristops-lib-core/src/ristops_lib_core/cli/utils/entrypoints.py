from importlib.metadata import entry_points
from typing import Any

from ristops_lib_core.cli.utils.command import ENTRYPOINT_COMMANDS_GROUP_NAME
from ristops_lib_core.utils import load_object


def load_entrypoint(group: str, name: str) -> str:
    """ Load entry point from group and name """

    entrypoints = entry_points(group=group, name=name)
    if len(entrypoints) != 1:
        raise ValueError(
            f"Invalid entrypoint configuration, expected exactly one entrypoint for {group=} {name=}, "
            f"found {len(entrypoints)}: {entrypoints.names}"
        )
    for entrypoint in entrypoints:
        return entrypoint.value
    raise ValueError("Invalid entrypoint configuration")


def load_command_entrypoint(name: str, suffix: str | None = None) -> str:
    """ Load command entry point value """
    group = ENTRYPOINT_COMMANDS_GROUP_NAME
    if suffix:
        group = f"{group}.{suffix}"
    return load_entrypoint(group=group.replace("-", "_"), name=name)


def load_command_entrypoint_object(name: str, suffix: str | None = None) -> Any:
    """ Load command entry point object """
    _path = load_command_entrypoint(name=name, suffix=suffix)
    return load_object(_path)


def get_group_entrypoint_names(group: str) -> list[str]:
    """ Get entry point names """
    entrypoints = entry_points(group=group)
    return [entrypoint.name for entrypoint in entrypoints]


def get_command_group_entrypoint_names(suffix: str | None = None) -> list[str]:
    """ Get command entry point names """
    group = ENTRYPOINT_COMMANDS_GROUP_NAME
    if suffix:
        group = f"{group}.{suffix}"
    return get_group_entrypoint_names(group=group)

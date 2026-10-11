import asyncio

import click
import pytest
from click.testing import CliRunner

import ristops_lib_core.cli.entrypoint as entrypoint_module
import ristops_lib_core.cli.start as start_module
import ristops_lib_core.cli.utils.command as command_module
import ristops_lib_core.cli.utils.entrypoints as entrypoints_module
from helpers import fake_entry_points
from ristops_lib_core.cli.utils.command import (
    ENTRYPOINT_COMMANDS_GROUP_NAME, MainGroup, async_command, get_command_path,
)
from ristops_lib_core.cli.utils.entrypoints import (
    get_command_group_entrypoint_names, get_group_entrypoint_names, load_command_entrypoint,
    load_command_entrypoint_object, load_entrypoint,
)

COMMANDS = ENTRYPOINT_COMMANDS_GROUP_NAME


class TestGetCommandPath:

    @staticmethod
    def context(*names: str) -> click.Context:
        ctx = None
        for name in names:
            ctx = click.Context(click.Command(name), info_name=name, parent=ctx)
        return ctx

    def test_a_top_level_command_is_just_its_name(self):
        assert get_command_path(self.context("ristops"), "start") == "start"

    def test_a_nested_command_is_dotted_under_its_group(self):
        assert get_command_path(self.context("ristops", "sql-database"), "generate-ddl") == "sql-database.generate-ddl"

    def test_underscores_become_hyphens(self):
        assert get_command_path(self.context("ristops", "sql_database"), "generate_ddl") == "sql-database.generate-ddl"


class TestMainGroup:

    @pytest.fixture
    def group(self, monkeypatch: pytest.MonkeyPatch) -> MainGroup:
        monkeypatch.setattr(command_module, "entry_points", fake_entry_points(
            (COMMANDS, "demo", "helpers:demo_command"),
            (COMMANDS, "broken", "helpers:not_a_command"),
            (COMMANDS, "missing", "helpers:no_such_object"),
            ("another.group", "ignored", "helpers:demo_command"),
        ))

        @click.group(cls=MainGroup, name="ristops")
        def main() -> None: ...

        @main.command()
        def builtin() -> None:
            click.echo("builtin ran")

        return main

    def test_lists_the_builtin_and_the_registered_commands(self, group: MainGroup):
        names = group.list_commands(click.Context(group))

        assert names[0] == "builtin"
        assert names[1:] == ["broken", "demo", "missing"]

    def test_only_the_commands_group_is_read(self, group: MainGroup):
        assert "ignored" not in group.list_commands(click.Context(group))

    def test_a_registered_command_is_loaded_when_asked_for(self, group: MainGroup):
        result = CliRunner().invoke(group, ["demo"])

        assert result.exit_code == 0
        assert result.output.strip() == "demo ran"

    def test_the_loaded_command_is_named_after_its_path(self, group: MainGroup):
        assert group.get_command(click.Context(group, info_name="ristops"), "demo").name == "demo"

    def test_a_builtin_command_still_works(self, group: MainGroup):
        assert CliRunner().invoke(group, ["builtin"]).output.strip() == "builtin ran"

    def test_an_unknown_command_is_a_usage_error(self, group: MainGroup):
        result = CliRunner().invoke(group, ["nothing"])

        assert result.exit_code == 2
        assert "No such command" in result.output

    def test_an_entry_point_that_is_not_a_command_is_rejected(self, group: MainGroup):
        result = CliRunner().invoke(group, ["broken"])

        assert result.exit_code != 0
        assert isinstance(result.exception, ValueError)
        assert "non-command object" in str(result.exception)

    def test_an_entry_point_that_cannot_be_imported_fails(self, group: MainGroup):
        result = CliRunner().invoke(group, ["missing"])

        assert isinstance(result.exception, AttributeError)


class TestAsyncCommand:

    def test_runs_the_coroutine_and_returns_its_result(self):
        @async_command
        async def work(value: int) -> int:
            await asyncio.sleep(0)
            return value * 2

        assert work(21) == 42

    def test_keeps_the_name_and_docstring(self):
        @async_command
        async def work() -> None:
            """Do the work."""

        assert work.__name__ == "work"
        assert work.__doc__ == "Do the work."

    def test_works_under_a_click_command(self):
        @click.command()
        @async_command
        async def command() -> None:
            click.echo("ran")

        assert CliRunner().invoke(command).output.strip() == "ran"

    def test_an_exception_from_the_coroutine_propagates(self):
        @async_command
        async def work() -> None:
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            work()


class TestEntrypoints:

    @pytest.fixture(autouse=True)
    def entries(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setattr(entrypoints_module, "entry_points", fake_entry_points(
            (f"{COMMANDS}.start", "be-demo", "helpers:demo_app_factory"),
            (f"{COMMANDS}.start", "be-other", "helpers:demo_command"),
            (f"{COMMANDS}.sql_database", "tables", "helpers:demo_command"),
            (COMMANDS, "start", "helpers:demo_command"),
            ("duplicated", "same", "helpers:demo_command"),
            ("duplicated", "same", "helpers:demo_app_factory"),
        ))

    def test_load_entrypoint_returns_its_value(self):
        assert load_entrypoint(f"{COMMANDS}.start", "be-demo") == "helpers:demo_app_factory"

    def test_load_entrypoint_requires_exactly_one_match(self):
        with pytest.raises(ValueError, match="expected exactly one entrypoint"):
            load_entrypoint(COMMANDS, "unknown")

    def test_load_entrypoint_rejects_duplicates(self):
        with pytest.raises(ValueError, match="found 2") as caught:
            load_entrypoint("duplicated", "same")

        assert "group='duplicated'" in str(caught.value)

    def test_the_command_entrypoint_group_gets_the_suffix(self):
        assert load_command_entrypoint("be-demo", suffix="start") == "helpers:demo_app_factory"

    def test_the_command_entrypoint_group_without_a_suffix(self):
        assert load_command_entrypoint("start") == "helpers:demo_command"

    def test_hyphens_in_the_suffix_become_underscores(self):
        assert load_command_entrypoint("tables", suffix="sql-database") == "helpers:demo_command"

    def test_loads_the_object_behind_the_entrypoint(self):
        factory = load_command_entrypoint_object("be-demo", suffix="start")

        assert factory() == "demo-app"

    def test_lists_the_names_of_a_group(self):
        assert get_group_entrypoint_names(f"{COMMANDS}.start") == ["be-demo", "be-other"]

    def test_lists_nothing_for_an_unknown_group(self):
        assert get_group_entrypoint_names("nothing") == []

    def test_lists_the_command_names_with_and_without_a_suffix(self):
        assert get_command_group_entrypoint_names(suffix="start") == ["be-demo", "be-other"]
        assert get_command_group_entrypoint_names() == ["start"]


class TestStart:

    @pytest.fixture
    def runs(self, monkeypatch: pytest.MonkeyPatch) -> list[dict]:
        calls = []
        monkeypatch.setattr(start_module, "load_command_entrypoint_object", lambda name, suffix: lambda: f"app:{name}")
        monkeypatch.setattr(start_module.uvicorn, "run", lambda app, **kwargs: calls.append({"app": app, **kwargs}))
        monkeypatch.setattr(start_module.start.params[0], "type", click.Choice(["be-demo"]))
        return calls

    def test_builds_the_app_and_serves_it_on_the_default_port(self, runs: list[dict]):
        result = CliRunner().invoke(start_module.start, ["be-demo"])

        assert result.exit_code == 0
        assert runs[0]["app"] == "app:be-demo"
        assert (runs[0]["host"], runs[0]["port"], runs[0]["root_path"]) == ("0.0.0.0", 8000, "")

    def test_uses_the_logging_configuration_with_the_request_context(self, runs: list[dict]):
        CliRunner().invoke(start_module.start, ["be-demo"])

        assert runs[0]["log_config"]["filters"]["context_filter"]

    @pytest.mark.parametrize("option", ["-p", "--port"])
    def test_takes_the_port_from_the_option(self, runs: list[dict], option: str):
        CliRunner().invoke(start_module.start, ["be-demo", option, "9001"])

        assert runs[0]["port"] == 9001

    def test_takes_the_port_from_the_environment(self, runs: list[dict]):
        CliRunner().invoke(start_module.start, ["be-demo"], env={"RISTOPS_PORT": "9002"})

        assert runs[0]["port"] == 9002

    def test_the_option_wins_over_the_environment(self, runs: list[dict]):
        CliRunner().invoke(start_module.start, ["be-demo", "-p", "9003"], env={"RISTOPS_PORT": "9002"})

        assert runs[0]["port"] == 9003

    def test_an_unknown_app_is_a_usage_error_and_nothing_starts(self, runs: list[dict]):
        result = CliRunner().invoke(start_module.start, ["be-unknown"])

        assert result.exit_code == 2
        assert "Invalid value" in result.output
        assert runs == []

    def test_the_app_name_is_required(self, runs: list[dict]):
        assert CliRunner().invoke(start_module.start, []).exit_code == 2

    def test_a_non_numeric_port_is_rejected(self, runs: list[dict]):
        assert CliRunner().invoke(start_module.start, ["be-demo", "-p", "abc"]).exit_code == 2


class TestMain:

    def test_the_group_is_called_ristops_and_uses_the_lazy_loader(self):
        assert entrypoint_module.main.name == "ristops"
        assert isinstance(entrypoint_module.main, MainGroup)

    def test_shows_its_help(self):
        result = CliRunner().invoke(entrypoint_module.main, ["--help"])

        assert result.exit_code == 0
        assert "RistOps command line interface" in result.output

    def test_configures_logging_before_running_a_command(self, monkeypatch: pytest.MonkeyPatch):
        calls = []
        monkeypatch.setattr(entrypoint_module, "configure_logging", lambda: calls.append("configured"))
        monkeypatch.setattr(
            command_module, "entry_points", fake_entry_points((COMMANDS, "demo", "helpers:demo_command")),
        )
        group = entrypoint_module.main.__class__(name="ristops", callback=entrypoint_module.main.callback)

        result = CliRunner().invoke(group, ["demo"])

        assert result.output.strip() == "demo ran"
        assert calls == ["configured"]

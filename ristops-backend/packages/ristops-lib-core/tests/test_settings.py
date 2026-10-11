import os
from pathlib import Path

import pytest
from pydantic_settings import SettingsConfigDict

from ristops_lib_core.settings import DOTENV_VAR, ENVVARS_PREFIX, BaseServiceSettings, _get_dotenv_path


class DemoSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(env_prefix=ENVVARS_PREFIX + "DEMO_", env_file=None)

    value: int = 1
    name: str = "default"


@pytest.fixture(autouse=True)
def fresh_settings_cache():
    BaseServiceSettings.get.cache_clear()
    yield
    BaseServiceSettings.get.cache_clear()


def test_prefix_and_dotenv_variable_names():
    assert ENVVARS_PREFIX == "RISTOPS_"
    assert DOTENV_VAR == "RISTOPS_ENV_PATH"


def test_defaults_are_used_without_environment():
    settings = DemoSettings.get()

    assert (settings.value, settings.name) == (1, "default")


def test_environment_overrides_defaults_and_is_parsed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RISTOPS_DEMO_VALUE", "42")
    monkeypatch.setenv("RISTOPS_DEMO_NAME", "from-env")

    settings = DemoSettings.get()

    assert (settings.value, settings.name) == (42, "from-env")


def test_get_returns_the_cached_instance():
    assert DemoSettings.get() is DemoSettings.get()


def test_get_does_not_see_environment_changes_after_the_first_call(monkeypatch: pytest.MonkeyPatch):
    first = DemoSettings.get()
    monkeypatch.setenv("RISTOPS_DEMO_VALUE", "7")

    assert DemoSettings.get().value == first.value == 1


def test_get_with_arguments_builds_a_separate_instance():
    assert DemoSettings.get(value=9).value == 9
    assert DemoSettings.get().value == 1


def test_unknown_fields_are_ignored():
    assert DemoSettings(unknown="x").value == 1


def test_invalid_value_is_rejected(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RISTOPS_DEMO_VALUE", "not-a-number")

    with pytest.raises(ValueError):
        DemoSettings()


class TestDotenvPath:

    def test_uses_the_variable_when_set(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv(DOTENV_VAR, "/somewhere/service.env")

        assert _get_dotenv_path() == Path("/somewhere/service.env")

    def test_falls_back_to_dotenv_in_the_working_directory(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        monkeypatch.delenv(DOTENV_VAR, raising=False)
        monkeypatch.chdir(tmp_path)

        assert _get_dotenv_path() == Path(os.getcwd()) / ".env"

    def test_an_empty_variable_counts_as_unset(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
        monkeypatch.setenv(DOTENV_VAR, "")
        monkeypatch.chdir(tmp_path)

        assert _get_dotenv_path() == Path(os.getcwd()) / ".env"

"""Versioned prompts: models, semantic versions and a registry backed by YAML files."""

import re
from abc import ABC, abstractmethod
from enum import StrEnum
from functools import total_ordering
from pathlib import Path
from typing import Iterable, Any

import yaml
from pydantic import BaseModel, ConfigDict, NonNegativeInt, model_validator


class PromptNotFoundError(ValueError):
    """Raised when a prompt, or the requested version of it, does not exist."""


class VersionedPrompt(BaseModel):
    """A prompt together with its name and the version it is stored under."""

    name: str
    version: str
    prompt: Prompt


class Prompt(BaseModel):
    """The content of a prompt: the system prompt and the model it is meant for."""

    system_prompt: str
    model: PromptModelConfig


class PromptModelConfig(BaseModel):
    """The model and the sampling settings a prompt is tuned for."""

    model_name: str
    temperature: float


def make_prompt_key(name: str, version: str) -> str:
    """Return the display key of a prompt version, as `<name>:<version>`."""
    return f"{name}:{version}"


_VERSION_RE = re.compile(r"v?([0-9]+)\.([0-9]+)\.([0-9]+)")


class VersionComponent(StrEnum):
    """The component of a semantic version that a bump increments."""

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


@total_ordering
class SemanticVersion(BaseModel):
    """An immutable MAJOR.MINOR.PATCH version, ordered by its components. Version 0.0.0 is not valid."""

    model_config = ConfigDict(frozen=True)

    major: NonNegativeInt
    minor: NonNegativeInt
    patch: NonNegativeInt

    @property
    def name(self) -> str:
        """Return the version as `MAJOR.MINOR.PATCH`."""
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def _key(self) -> tuple[int, int, int]:
        return self.major, self.minor, self.patch

    @model_validator(mode="after")
    def _reject_zero_version(self) -> SemanticVersion:
        if not (self.major or self.minor or self.patch):
            raise ValueError("Version 0.0.0 is not valid")
        return self

    @classmethod
    def initial(cls) -> SemanticVersion:
        """Return the first version of a prompt, 1.0.0."""
        return cls(major=1, minor=0, patch=0)

    @classmethod
    def parse(cls, value: str | Iterable) -> SemanticVersion:
        """Build a version from a `MAJOR.MINOR.PATCH` string, with an optional leading `v`, or from three components.

        Raises ValueError if the value is malformed.
        """
        if isinstance(value, str):
            match = _VERSION_RE.fullmatch(value.strip())
            if match is None:
                raise ValueError(
                    f"Invalid version string {value!r}, expected 'MAJOR.MINOR.PATCH'"
                )
            value = match.groups()

        parts = tuple(map(int, value))
        if len(parts) != 3:
            raise ValueError(
                f"Expected 3 components (major, minor, patch), got {len(parts)}: {parts!r}"
            )

        major, minor, patch = parts
        return cls(major=major, minor=minor, patch=patch)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return self._key == other._key

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, SemanticVersion):
            return NotImplemented
        return self._key < other._key

    def __hash__(self) -> int:
        return hash(self._key)

    def bump_major(self) -> SemanticVersion:
        """Return the next major version, resetting minor and patch."""
        return SemanticVersion(major=self.major + 1, minor=0, patch=0)

    def bump_minor(self) -> SemanticVersion:
        """Return the next minor version, resetting patch."""
        return SemanticVersion(major=self.major, minor=self.minor + 1, patch=0)

    def bump_patch(self) -> SemanticVersion:
        """Return the next patch version."""
        return SemanticVersion(major=self.major, minor=self.minor, patch=self.patch + 1)

    def bump(self, component: VersionComponent) -> SemanticVersion:
        """Return the version bumped on the given component."""
        match component:
            case VersionComponent.MAJOR:
                return self.bump_major()
            case VersionComponent.MINOR:
                return self.bump_minor()
            case VersionComponent.PATCH:
                return self.bump_patch()
            case _:
                raise ValueError(f"Unknown component {component}")


class PromptRegistry(ABC):
    """Shared behavior of prompt registries, leaving only the storage to subclasses.

    Implements `load` and `save`, that is version resolution and bumping, on top of three hooks that a subclass
    provides: `_resolve_latest_version`, `_load` and `_save`.
    """

    def load(self, name: str, version: str | None = None) -> VersionedPrompt:
        """Return the prompt with the given name and version, or its latest version when none is given.

        Raises PromptNotFoundError if it does not exist.
        """
        _version = self._resolve_version(name, version)
        prompt = self._load(name, _version)
        return VersionedPrompt(
            name=name,
            version=_version.name,
            prompt=prompt,
        )

    def _resolve_version(self, name: str, version: str | None = None) -> SemanticVersion:
        """Return the requested version, parsed, or the latest one when none is given."""
        if version is None:
            return self._find_latest_version(name)
        return SemanticVersion.parse(version)

    def _find_latest_version(self, name: str) -> SemanticVersion:
        """Return the latest version of the name. Raises PromptNotFoundError if it has none."""
        latest_version = self._resolve_latest_version(name)
        if latest_version is None:
            raise PromptNotFoundError(f"Cannot find any prompt with name `{name}`")
        return latest_version

    def save(self, name: str, prompt: Prompt, component: VersionComponent | None = None) -> SemanticVersion:
        """Store the prompt as a new version of the name and return that version.

        The first save creates 1.0.0. Later saves bump the latest version on the given component, minor by default.
        """
        latest_version = self._resolve_latest_version(name)
        if latest_version is None:
            version = SemanticVersion.initial()
        else:
            version = latest_version.bump(component or VersionComponent.MINOR)
        self._save(name, version, prompt)
        return version

    @abstractmethod
    def _resolve_latest_version(self, name: str) -> SemanticVersion | None:
        """Return the latest stored version of the name, or None when the name has no versions."""

    @abstractmethod
    def _load(self, name: str, version: SemanticVersion) -> Prompt:
        """Return the stored prompt of the given version. Raises PromptNotFoundError if it does not exist."""

    @abstractmethod
    def _save(self, name: str, version: SemanticVersion, prompt: Prompt) -> None:
        """Store the prompt under the given version. The version is always a new one, chosen by `save`."""


class YamlPromptRegistry(PromptRegistry):
    """A prompt registry backed by YAML files in a directory, one per version.

    Files are named `<name>.<major>.<minor>.<patch>.yaml`.
    """

    _EXTENSION = "yaml"

    def __init__(self, location: Path):
        """Create a registry that reads and writes prompts in the given directory."""
        self._location = location

    def _resolve_latest_version(self, name: str) -> SemanticVersion | None:
        # <name>.<major>.<minor>.<patch>.yaml
        pattern = re.compile(rf"^{re.escape(name)}\.(\d+)\.(\d+)\.(\d+)\.{YamlPromptRegistry._EXTENSION}$")

        latest_version: SemanticVersion | None = None
        for file in self._location.glob(f"{name}.*.{YamlPromptRegistry._EXTENSION}"):
            if not (_match := pattern.match(file.name)):
                continue
            version = SemanticVersion.parse(_match.groups())
            if latest_version is None or version > latest_version:
                latest_version = version

        return latest_version

    def _load(self, name: str, version: SemanticVersion) -> Prompt:
        filepath = self._make_filename(name, version)
        if not filepath.is_file():
            raise PromptNotFoundError(f"Cannot find prompt `{make_prompt_key(name, version.name)}` at {self._location}")
        with filepath.open("r") as f:
            data = yaml.safe_load(f)
        return Prompt.model_validate(data)

    def _make_filename(self, name: str, version: SemanticVersion) -> Path:
        return self._location / f"{name}.{version.name}.{YamlPromptRegistry._EXTENSION}"

    def _save(self, name: str, version: SemanticVersion, prompt: Prompt) -> None:
        filepath = self._make_filename(name, version)
        with filepath.open("x") as file:
            yaml.safe_dump(prompt.model_dump(mode="json"), file, sort_keys=False)

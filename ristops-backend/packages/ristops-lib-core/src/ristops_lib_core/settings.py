import logging
import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_logger = logging.getLogger(__name__)
ENVVARS_PREFIX = "RISTOPS_"
DOTENV_VAR = ENVVARS_PREFIX + "ENV_PATH"


def _get_dotenv_path() -> Path:
    """ Resolve .env file to absolute path. """
    env_path = os.environ.get(DOTENV_VAR)
    if not env_path:
        _env_path = Path(os.getcwd()) / ".env"
        _logger.debug("No .env path set with variable %s, defaulting to %s", DOTENV_VAR, _env_path)
    else:
        _env_path = Path(env_path)
    _logger.info("Using .env path %s", _env_path)
    if not _env_path.is_file():
        _logger.debug("No .env file found at %s", _env_path)
    return _env_path


DOTENV_PATH = _get_dotenv_path()


class BaseServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX,
        env_file=DOTENV_PATH,
        extra="ignore",
    )

    @classmethod
    @lru_cache
    def get(cls, **kwargs):
        return cls(**kwargs)

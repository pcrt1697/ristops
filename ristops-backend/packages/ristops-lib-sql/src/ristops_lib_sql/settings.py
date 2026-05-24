from pydantic import Field
from pydantic_settings import SettingsConfigDict

from ristops_lib_core.settings import BaseServiceSettings, ENVVARS_PREFIX


class DatabaseSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX + "PG_",
    )

    host: str = Field(
        description="Database host address",
    )
    user: str = Field(
        description="Database user",
    )
    pwd: str = Field(
        description="Database password",
    )
    db_name: str = Field(
        description="Database name",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode for SQLAlchemy engine",
    )

    def get_database_url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.pwd}@{self.host}/{self.db_name}"


class ConsumerGroupSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX + "PG_",
    )

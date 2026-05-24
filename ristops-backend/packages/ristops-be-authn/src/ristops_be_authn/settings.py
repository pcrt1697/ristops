from pathlib import Path

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from ristops_lib_core.settings import BaseServiceSettings, ENVVARS_PREFIX
from ristops_lib_redis.settings import REDIS_STREAM_PREFIX, BaseRedisProducerSettings


class JwtSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX + "JWT_",
    )

    access_expiration_m: float = Field(
        default=15,
        description="The expiration time (minutes) of the access token.",
        gt=0.0,
    )
    refresh_expiration_h: float = Field(
        default=24,
        description="The expiration time (hours) of the refresh token.",
        gt=0.0,
    )
    keys_location: Path = Field(
        description="Location of the JWT access token key file.",
    )

    @property
    def private_key_location(self):
        return self.keys_location / "ec_private.pem"

    @property
    def public_key_location(self):
        return self.keys_location / "ec_public.pem"

    @property
    def refresh_key_location(self):
        return self.keys_location / "ec_refresh.pem"


class BackendServiceSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX + "BE_",
    )

    authz_url: str


class UserProducerSettings(BaseRedisProducerSettings):
    model_config = SettingsConfigDict(
        env_prefix=REDIS_STREAM_PREFIX + "USER_",
    )
    stream: str = Field("auth:users", description="Redis stream name for users operations")

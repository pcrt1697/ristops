from pydantic import Field
from pydantic_settings import SettingsConfigDict

from ristops_lib_core.settings import BaseServiceSettings, ENVVARS_PREFIX
from ristops_lib_redis.settings import REDIS_STREAM_PREFIX, BaseRedisProducerSettings


class BackendServiceSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX + "BE_",
    )

    authn_url: str = Field(
        description="The authentication service url.",
    )
    authz_url: str = Field(
        description="The authorization service url.",
    )


class ResourceLifecycleProducerSettings(BaseRedisProducerSettings):
    """Redis stream producer settings for resource lifecycle events."""

    model_config = SettingsConfigDict(
        env_prefix=REDIS_STREAM_PREFIX + "RESOURCE_LC_",
    )
    stream: str = Field("resource:lifecycle", description="Redis stream name for resource lifecycle events")

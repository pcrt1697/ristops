from pydantic import Field
from pydantic_settings import SettingsConfigDict

from ristops_lib_core.settings import BaseServiceSettings, ENVVARS_PREFIX
from ristops_lib_redis.settings import REDIS_STREAM_PREFIX, BaseRedisProducerSettings, BaseRedisConsumerSettings


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


class VenueLifecycleConsumerSettings(BaseRedisConsumerSettings):
    """Redis stream consumer settings for venue lifecycle events."""

    model_config = SettingsConfigDict(
        env_prefix=REDIS_STREAM_PREFIX + "VENUE_LC_",
    )
    stream: str = Field("venue:lifecycle", description="Redis stream name for venue lifecycle events")
    group: str = Field("reservation", description="Redis stream consumer group name for venue operations")
    name: str = Field("reservation", description="Redis consumer name for venue operations")
    log_payload: bool = True

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from ristops_lib_core.settings import BaseServiceSettings, ENVVARS_PREFIX
from ristops_lib_redis.settings import BaseRedisConsumerSettings, REDIS_STREAM_PREFIX

REDIS_CONSUMER_PREFIX = ENVVARS_PREFIX + "REDIS_CONSUMER_"


class BackendServiceSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX + "BE_",
    )
    authn_url: str = Field(
        description="The authentication service url.",
    )


class UserLifecycleConsumerSettings(BaseRedisConsumerSettings):
    model_config = SettingsConfigDict(
        env_prefix=REDIS_STREAM_PREFIX + "USER_LC_",
    )
    stream: str = Field("user:lifecycle", description="Redis stream name for user lifecycle events")
    group: str = Field("authz", description="Redis stream consumer group name for user operations")
    name: str = Field("authz", description="Redis consumer name for user operations")
    log_payload: bool = True


class ResourceLifecycleConsumerSettings(BaseRedisConsumerSettings):
    model_config = SettingsConfigDict(
        env_prefix=REDIS_STREAM_PREFIX + "RESOURCE_LC_",
    )
    stream: str = Field("resource:lifecycle", description="Redis stream name for resource lifecycle events")
    group: str = Field("authz", description="Redis stream consumer group name for resource operations")
    name: str = Field("authz", description="Redis consumer name for resource operations")
    log_payload: bool = True

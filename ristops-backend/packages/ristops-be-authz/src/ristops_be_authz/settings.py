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


class Neo4jSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX + "NEO4J_",
    )
    host: str = Field(description="Database host address")
    user: str = Field("neo4j", description="Database user")
    pwd: str = Field(description="Database password")

    def get_url(self):
        return f"neo4j://{self.host}"


class RedisUserConsumerSettings(BaseRedisConsumerSettings):
    model_config = SettingsConfigDict(
        env_prefix=REDIS_STREAM_PREFIX + "USER_",
    )
    stream: str = Field("auth:users", description="Redis stream name for user operations")
    group: str = Field("authz", description="Redis stream consumer group name for user operations")
    log_payload: bool = True


class RedisResourceConsumerSettings(BaseRedisConsumerSettings):
    model_config = SettingsConfigDict(
        env_prefix=REDIS_STREAM_PREFIX + "RESOURCE_",
    )
    stream: str = Field("auth:resources", description="Redis stream name for resources operations")
    group: str = Field("authz", description="Redis stream consumer group name for resource operations")
    log_payload: bool = True

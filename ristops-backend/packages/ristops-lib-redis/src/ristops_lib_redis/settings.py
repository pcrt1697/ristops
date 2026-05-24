from uuid import uuid4

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from ristops_lib_core.settings import BaseServiceSettings, ENVVARS_PREFIX

REDIS_PREFIX = ENVVARS_PREFIX + "REDIS_"
REDIS_STREAM_PREFIX = REDIS_PREFIX + "STREAM_"


class RedisSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=REDIS_PREFIX,
    )

    url: str = Field(description="Redis url for user operations", examples=["redis://localhost:6379"])


class BaseRedisConsumerSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=REDIS_STREAM_PREFIX,
    )
    stream: str = Field(description="Redis stream name")
    group: str = Field(description="Redis stream consumer group name")
    name: str = Field(default_factory=uuid4, description="Redis consumer name")
    wait_ms: int = Field(30_000, description="Time in milliseconds to wait for a message")
    retry_idle_ms: int = Field(30_000, description="For stale messages, amount of milliseconds to read backward")
    batch_size: int = Field(10, description="Batch size for reading messages")
    log_payload: bool = Field(False, description="If true, the message payload is logged before processing")


class BaseRedisProducerSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=REDIS_STREAM_PREFIX,
    )
    stream: str = Field(description="Redis stream name")

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from ristops_lib_core.settings import BaseServiceSettings, ENVVARS_PREFIX


class Neo4jSettings(BaseServiceSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENVVARS_PREFIX + "NEO4J_",
    )
    host: str = Field(description="Database host address")
    user: str = Field("neo4j", description="Database user")
    pwd: str = Field(description="Database password")

    def get_url(self):
        return f"neo4j://{self.host}"

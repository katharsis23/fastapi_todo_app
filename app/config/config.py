from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Postgresql_Config(BaseSettings):
    db_url: str = Field(alias="DATABASE_URL")

    model_config = SettingsConfigDict(
        title="PostgreSQL credential manager",
        env_file=None
    )


POSTGRESQL_CONFIG = Postgresql_Config()

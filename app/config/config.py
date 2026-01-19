from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


class Postgresql_Config(BaseSettings):
    db_url: str = Field(alias="DATABASE_URL")

    model_config = SettingsConfigDict(
        title="PostgreSQL credential manager",
        env_file=None
    )


POSTGRESQL_CONFIG = Postgresql_Config()


class JWT_Config(BaseSettings):
    secret_key: SecretStr = Field(alias="SECRET_KEY")
    algorithm: str = Field(alias="ALGORITHM")
    expiration_time: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    model_config = SettingsConfigDict(
        title="JWT configuration",
        env_file=None
    )


JWT_CONFIG = JWT_Config()

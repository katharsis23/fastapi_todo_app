from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


class PostgresqlConfig(BaseSettings):
    db_url: str = Field(alias="DATABASE_URL")

    model_config = SettingsConfigDict(
        title="PostgreSQL credential manager",
        env_file=None
    )


POSTGRESQL_CONFIG = PostgresqlConfig()


class JWTConfig(BaseSettings):
    secret_key: SecretStr = Field(alias="SECRET_KEY")
    algorithm: str = Field(alias="ALGORITHM")
    expiration_time: int = Field(alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    model_config = SettingsConfigDict(
        title="JWT configuration",
        env_file=None
    )


JWT_CONFIG = JWTConfig()


class S3Config(BaseSettings):
    endpoint_url: str = Field(alias="S3_ENDPOINT_URL")
    access_key: str = Field(alias="MINIO_ROOT_USER")
    secret_key: SecretStr = Field(alias="MINIO_ROOT_PASSWORD")
    bucket_notes: str = Field(alias="S3_BUCKET_NOTES")
    bucket_avatars: str = Field(alias="S3_BUCKET_AVATARS")

    model_config = SettingsConfigDict(
        title="S3 configuration",
        env_file=None
    )


S3_CONFIG = S3Config()


class RedisConfig(BaseSettings):
    redis_url: SecretStr = Field(alias="REDIS_URL")

    model_config = SettingsConfigDict(
        title="Redis configuration",
        env_file=None
    )


REDIS_CONFIG = RedisConfig()


class SMTPConfig(BaseSettings):
    host: str = Field(alias="SMTP_HOST")
    port: str = Field(alias="SMTP_PORT")
    user: str = Field(alias="SMTP_USER")
    password: SecretStr = Field(alias="SMTP_PASSWORD")
    from_: str = Field(alias="SMTP_FROM")

    model_config = SettingsConfigDict(
        title="SMTP configuration",
        env_file=None
    )


SMTPCONFIG = SMTPConfig()

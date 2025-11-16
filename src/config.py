import os
from functools import lru_cache

from pydantic import SecretStr, AnyHttpUrl, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


class Security(BaseSettings):
    jwt_issuer: str
    jwt_secret_key: SecretStr
    jwt_access_token_expire_secs: int
    refresh_token_expire_secs: int
    password_bcrypt_rounds: int
    allowed_hosts: list[str]
    backend_cors_origins: list[AnyHttpUrl]

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="SECURITY__", extra="ignore"
    )


class Database(BaseSettings):
    hostname: str
    username: str
    password: SecretStr
    port: int
    db: str

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="DATABASE__", extra="ignore"
    )


class Settings(BaseSettings):
    debug: bool = False
    database: Database = Field(Database)
    security: Security = Field(Security)

    @computed_field
    @property
    def sqlalchemy_database_uri(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.database.username,
            password=self.database.password.get_secret_value(),
            host=self.database.hostname,
            port=self.database.port,
            database=self.database.db,
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

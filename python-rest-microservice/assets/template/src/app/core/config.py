"""Application settings.

All configuration comes from environment variables (12-factor). A local, uncommitted
``.env`` file is supported for development convenience only. Secrets use ``SecretStr``
so they are never printed in logs or reprs.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    service_name: str = "example-service"
    environment: Literal["local", "test", "dev", "staging", "prod"] = "local"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = True

    # Database — injected by the runtime (cloud secret store → env var).
    database_url: SecretStr = SecretStr("postgresql+asyncpg://postgres:postgres@localhost:5432/app")
    database_pool_size: int = Field(default=5, ge=1)
    database_echo: bool = False

    # Interactive docs (/docs, /openapi.json). Always disabled when environment == "prod".
    docs_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings (cached). Override in tests via ``create_app``."""
    return Settings()

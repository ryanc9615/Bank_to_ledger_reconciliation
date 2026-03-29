from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application settings.

    Values are loaded from environment variables and/or a local .env file.
    This gives us one typed source of truth for runtime configuration.
    """

    app_name: str = "bank-to-ledger-reconciliation-api"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+psycopg://ryangael@localhost:5432/recon_dev"
    )

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cache settings so they are constructed once per process.
    """
    return Settings()
"""Environment-backed application settings, inspired by GraphOne's config boundary."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_env: Literal["development", "test", "production"] = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite+aiosqlite:///./data/xsentiment.db"
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=5, ge=0, le=100)
    db_pool_timeout_seconds: int = Field(default=30, ge=1, le=300)
    http_timeout_seconds: float = Field(default=20, gt=0, le=180)
    http_max_concurrency: int = Field(default=8, ge=1, le=64)
    http_max_retries: int = Field(default=3, ge=0, le=8)
    http_max_response_bytes: int = Field(default=5_000_000, ge=1_024, le=50_000_000)
    apify_api_token: SecretStr | None = None
    apify_actor_id: str | None = None
    tavily_api_key: SecretStr | None = None
    exa_api_key: SecretStr | None = None
    price_provider: str | None = None
    price_provider_api_key: SecretStr | None = None
    asset_symbol: str | None = None
    asset_class: str | None = None

    @field_validator(
        "apify_api_token",
        "apify_actor_id",
        "tavily_api_key",
        "exa_api_key",
        "price_provider",
        "price_provider_api_key",
        "asset_symbol",
        "asset_class",
        mode="before",
    )
    @classmethod
    def blank_optional_values_become_none(cls, value):
        """Treat blank .env entries as missing instead of configured credentials."""
        if isinstance(value, str) and not value.strip():
            return None
        return value.strip() if isinstance(value, str) else value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return one cached, validated configuration instance."""
    return Settings()

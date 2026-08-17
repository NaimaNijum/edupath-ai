from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EduPath AI"
    app_env: str = "development"
    debug: bool = True

    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"

    database_url: str
    redis_url: str
    gemini_api_key: str
    # These defaults are verified against the Gemini API model catalogue.
    # Deployments may override them when their project enables different models.
    gemini_model: str = "gemini-3.6-flash"
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 1536
    gemini_temperature: float = 0.2
    gemini_request_timeout_seconds: float = 60.0
    # Hard cap on Gemini generateContent calls per workflow run. The
    # opportunity_discovery plan needs 1 supervisor planning call + up to 7
    # agent calls (8 total); the default leaves a little headroom while still
    # protecting the free-tier quota from runaway/looping graphs.
    max_llm_calls_per_workflow: int = 10
    web_search_api_url: str | None = None
    web_search_api_key: str | None = None
    search_timeout_seconds: float = 15.0
    redis_socket_timeout_seconds: float = 2.0
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str) and value.lower() in {"release", "production", "prod"}:
            return False
        if isinstance(value, str) and value.lower() in {"development", "dev"}:
            return True
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

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
    # OpenRouter handles both text generation and embeddings.
    embedding_model: str = "openai/text-embedding-3-small"
    embedding_dimensions: int = 1536
    # --- OpenRouter (text generation + embeddings) --------------------------
    openrouter_api_key: str
    # openrouter/free is an auto-router that resiliently routes each call to
    # whichever free model is currently available, instead of pinning one
    # model that could later be deprecated.
    openrouter_model: str = "openrouter/free"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_temperature: float = 0.2
    openrouter_request_timeout_seconds: float = 60.0
    # Hard cap on LLM generation calls per workflow run. The
    # opportunity_discovery plan needs 1 supervisor planning call + up to 8
    # agent calls (ranking_agent is deterministic Python and makes no LLM
    # call); the default leaves a little headroom while still protecting the
    # free-tier quota from runaway/looping graphs.
    max_llm_calls_per_workflow: int = 12
    web_search_api_url: str | None = None
    web_search_api_key: str | None = None
    search_timeout_seconds: float = 15.0
    redis_socket_timeout_seconds: float = 2.0
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # --- Auth (Google OAuth + dev-mock fallback) ---------------------------
    # When google_client_id/secret are unset, /api/v1/auth/config reports
    # dev-mock mode instead of real OAuth, so the app stays runnable without
    # Google credentials.
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"
    frontend_url: str = "http://localhost:8501"
    jwt_secret_key: str
    jwt_expiry_minutes: int = 1440

    # --- Ranking Agent weights (must sum to 1.0) ----------------------------
    ranking_weight_research_match: float = 0.30
    ranking_weight_eligibility: float = 0.20
    ranking_weight_funding: float = 0.20
    ranking_weight_professor_match: float = 0.15
    ranking_weight_university_tier: float = 0.10
    ranking_weight_deadline_urgency: float = 0.05

    # --- Document upload ------------------------------------------------
    max_document_size_mb: float = 10.0

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

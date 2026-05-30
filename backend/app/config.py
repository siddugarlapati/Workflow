"""
WorkFlow — Application Settings
Uses pydantic-settings for type-safe, validated configuration.
"""
from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Supabase ───────────────────────────────────────────────────────────────
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    database_url: str  # asyncpg connection string

    # ── Auth ───────────────────────────────────────────────────────────────────
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours

    # ── Ollama ─────────────────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"

    # ── Gemini ─────────────────────────────────────────────────────────────────
    gemini_api_key: Optional[str] = None

    # ── App ────────────────────────────────────────────────────────────────────
    app_env: Literal["development", "production", "test"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_url: str = "http://localhost:8501"

    # ── Logging ────────────────────────────────────────────────────────────────
    log_level: str = "INFO"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def cors_origins(self) -> list[str]:
        return [
            self.frontend_url,
            "http://localhost:8501",
            "http://127.0.0.1:8501",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://workflow-platform-ashen.vercel.app",
            "https://workflow-platform-ashen.vercel.app/",
            "https://workflow-platform-ashen.vercel.app:443",
            "https://workflow-platform-9crmi70wo-siddugarlapati09-gmailcoms-projects.vercel.app",
            "https://workflow-platform-9crmi70wo-siddugarlapati09-gmailcoms-projects.vercel.app/",
        ]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — import this everywhere."""
    return Settings()  # type: ignore[call-arg]


settings = get_settings()

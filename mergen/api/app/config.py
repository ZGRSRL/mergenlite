"""
MergenLite Application Settings
================================
Single source of truth for all configuration.
Uses pydantic-settings to load from environment variables / .env files.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# ---------------------------------------------------------------------------
# Eagerly load .env so that os.getenv works for default values below
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    _project_root = Path(__file__).resolve().parent.parent.parent.parent
    _env_candidates = [
        _project_root / "mergen" / ".env",
        _project_root / ".env",
        Path("mergen/.env"),
        Path(".env"),
    ]
    for _p in _env_candidates:
        if _p.exists():
            load_dotenv(_p, override=True)
            break
except ImportError:
    pass


class Settings(BaseSettings):
    """
    All settings are populated from environment variables.
    Docker Compose injects them; for local dev the .env file is loaded above.
    """

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        case_sensitive=False,
    )

    # -- Application ----------------------------------------------------------
    env: str = os.getenv("ENV", "dev")
    api_port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # -- Database -------------------------------------------------------------
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    postgres_db: str = os.getenv("POSTGRES_DB", "mergenlite")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")

    # -- LLM ------------------------------------------------------------------
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    ollama_host: str = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
    generator_model: str = os.getenv("GENERATOR_MODEL", "gpt-4o")
    extractor_model: str = os.getenv("EXTRACTOR_MODEL", "gpt-4o-mini")

    # -- SAM.gov --------------------------------------------------------------
    sam_api_key: Optional[str] = os.getenv("SAM_API_KEY")
    sam_enabled: bool = os.getenv("SAM_ENABLED", "true").lower() == "true"

    # -- Amadeus --------------------------------------------------------------
    amadeus_api_key: Optional[str] = os.getenv("AMADEUS_API_KEY")
    amadeus_api_secret: Optional[str] = os.getenv("AMADEUS_API_SECRET")
    amadeus_env: str = os.getenv("AMADEUS_ENV", "production")

    # -- Email / SMTP ---------------------------------------------------------
    smtp_host: Optional[str] = os.getenv("SMTP_HOST")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: Optional[str] = os.getenv("SMTP_USERNAME")
    smtp_password: Optional[str] = os.getenv("SMTP_PASSWORD")
    smtp_use_tls: bool = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "noreply@mergenlite.com")
    pipeline_notification_email: Optional[str] = os.getenv("PIPELINE_NOTIFICATION_EMAIL")

    # -- Telegram Notifications -----------------------------------------------
    telegram_bot_token: Optional[str] = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = os.getenv("TELEGRAM_CHAT_ID")
    telegram_enabled: bool = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"

    # -- Feature flags --------------------------------------------------------
    hotel_match_use_autogen: bool = os.getenv("HOTEL_MATCH_USE_AUTOGEN", "false").lower() == "true"

    # =========================================================================
    # Computed properties
    # =========================================================================
    @property
    def database_url(self) -> str:
        """
        Priority:
        1. DATABASE_URL env var (set by Docker Compose / Cloud Run)
        2. Constructed from individual POSTGRES_* vars
        """
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            # Normalise driver prefix for sync SQLAlchemy
            if "postgresql+asyncpg://" in db_url:
                db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
            return db_url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def is_production(self) -> bool:
        return self.env in ("prod", "production")


settings = Settings()

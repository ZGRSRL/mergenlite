import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env dosyasını yükle (mergen/.env)
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent.parent
    mergen_env_path = project_root / "mergen" / ".env"
    if mergen_env_path.exists():
        load_dotenv(mergen_env_path, override=True)
        print(f"[config.py] Loaded .env from: {mergen_env_path}")
    else:
        # Alternatif yolları dene
        alt_paths = [project_root / ".env", Path("mergen/.env"), Path(".env")]
        for alt_path in alt_paths:
            if alt_path.exists():
                load_dotenv(alt_path, override=True)
                print(f"[config.py] Loaded .env from: {alt_path}")
                break
except ImportError:
    print("[config.py] python-dotenv not installed")
except Exception as e:
    print(f"[config.py] Error loading .env: {e}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        case_sensitive=False,
    )
    # API
    api_port: int = 8000
    env: str = "dev"
    
    # Database - .env'den override edilebilir
    postgres_user: str = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "postgres"))
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "postgres"))
    postgres_db: str = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "ZGR_AI"))
    postgres_port: int = int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", "5432")))
    postgres_host: str = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost"))
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # LLM
    llm_provider: str = "ollama"
    ollama_host: str = "http://host.docker.internal:11434"
    generator_model: str = "llama3"
    extractor_model: str = "llama3"
    
    # SAM Integration (future)
    sam_enabled: bool = False

    # Amadeus
    amadeus_api_key: Optional[str] = os.getenv("AMADEUS_API_KEY")
    amadeus_api_secret: Optional[str] = os.getenv("AMADEUS_API_SECRET")
    amadeus_env: str = os.getenv("AMADEUS_ENV", "test")
    
    # Email/SMTP Settings - BaseSettings will load from env vars automatically
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    smtp_from_email: Optional[str] = "noreply@mergenlite.com"
    pipeline_notification_email: Optional[str] = None
    hotel_match_use_autogen: bool = False
    
    def model_post_init(self, __context):
        """Override to load from os.getenv as fallback if BaseSettings didn't load them."""
        # Fallback to os.getenv if BaseSettings didn't load from env file
        if not self.smtp_host:
            self.smtp_host = os.getenv("SMTP_HOST")
        if not self.smtp_username:
            self.smtp_username = os.getenv("SMTP_USERNAME")
        if not self.smtp_password:
            self.smtp_password = os.getenv("SMTP_PASSWORD")
        if not self.pipeline_notification_email:
            self.pipeline_notification_email = os.getenv("PIPELINE_NOTIFICATION_EMAIL")
        if os.getenv("SMTP_PORT"):
            try:
                self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
            except (ValueError, TypeError):
                pass
        if os.getenv("SMTP_USE_TLS"):
            self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        if os.getenv("SMTP_FROM_EMAIL"):
            self.smtp_from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@mergenlite.com")
        # Hotel match toggle
        if os.getenv("HOTEL_MATCH_USE_AUTOGEN"):
            self.hotel_match_use_autogen = os.getenv("HOTEL_MATCH_USE_AUTOGEN", "false").lower() == "true"
    
    @property
    def database_url(self) -> str:
        # If DATABASE_URL is set in environment, use it directly (Cloud Run)
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            # Convert asyncpg URL to psycopg2 URL for sync SQLAlchemy
            if "postgresql+asyncpg://" in db_url:
                db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
            elif db_url.startswith("postgresql://"):
                # Already correct format
                pass
            return db_url
        # Otherwise, construct from individual components
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    

settings = Settings()

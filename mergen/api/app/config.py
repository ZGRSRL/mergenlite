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
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    

settings = Settings()

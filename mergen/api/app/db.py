"""
MergenLite Database Module
==========================
Single source of database connectivity.
- Reads DATABASE_URL from environment (docker-compose / Cloud Run)
- Falls back to individual POSTGRES_* vars via config.Settings
- Connection pool tuned for production (pre-ping, recycle, pool size)
- Provides `get_db` FastAPI dependency
- `init_pgvector()` helper to enable pgvector extension on first run
- `check_db_health()` for readiness probes
"""

import logging
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from .config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,       # verify connections before checkout
    pool_recycle=300,          # recycle connections every 5 min
    pool_size=10,              # maintain up to 10 connections
    max_overflow=20,           # allow up to 20 extra connections under load
    echo=settings.env == "dev",
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ---------------------------------------------------------------------------
# Declarative base — all models inherit from this
# ---------------------------------------------------------------------------
Base = declarative_base()


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db():
    """Yield a SQLAlchemy session for a single request, then close."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Context-manager variant (for background tasks / scripts)
# ---------------------------------------------------------------------------
@contextmanager
def get_db_session():
    """Context-manager wrapper around SessionLocal for non-FastAPI usage."""
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# pgvector initialisation
# ---------------------------------------------------------------------------
def init_pgvector() -> bool:
    """
    Enable the pgvector extension in the connected database.
    Safe to call multiple times (CREATE EXTENSION IF NOT EXISTS).
    Returns True on success, False on failure.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        logger.info("[db] pgvector extension enabled successfully")
        return True
    except Exception as exc:
        logger.warning("[db] Could not enable pgvector: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
def check_db_health() -> dict:
    """
    Quick health check — runs `SELECT 1` and returns status dict.
    Used by /health and Docker HEALTHCHECK.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"database": "healthy"}
    except Exception as exc:
        logger.error("[db] Health check failed: %s", exc)
        return {"database": "unhealthy", "error": str(exc)}

"""
MergenLite FastAPI Application
===============================
Entry point for the backend.
- Loads env → config → routes
- Runs Alembic migrations on startup
- Enables pgvector extension
- Mounts static files for generated outputs (PDF / JSON)
"""

import logging
import os
import subprocess
import sys
import traceback
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ---------------------------------------------------------------------------
# Early env loading (before any internal imports)
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv

    _project_root = Path(__file__).resolve().parent.parent.parent.parent
    for _p in [_project_root / "mergen" / ".env", _project_root / ".env", Path(".env")]:
        if _p.exists():
            load_dotenv(_p, override=True)
            break
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Internal imports
# ---------------------------------------------------------------------------
from .config import settings  # noqa: E402
from .db import init_pgvector, check_db_health  # noqa: E402

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Import routes
# ---------------------------------------------------------------------------
try:
    from .routes import (
        health,
        ingest,
        compliance,
        proposal,
        search,
        opportunities,
        proxy,
        pipeline,
        dashboard,
        jobs,
        communications,
    )
    logger.info("[main] All route modules imported successfully")
except Exception as exc:
    logger.error("[main] Failed to import routes: %s", exc)
    traceback.print_exc()
    raise

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = FastAPI(
    title="MergenLite API",
    description="RFQ / SOW Analysis and Proposal Generation — Production Backend",
    version="2.0.0",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
_allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global Exception Handler
# ---------------------------------------------------------------------------
from .middleware import ExceptionHandlerMiddleware  # noqa: E402

app.add_middleware(ExceptionHandlerMiddleware)
logger.info("[main] Global exception handler middleware registered ✓")

# ---------------------------------------------------------------------------
# Static file mount for generated outputs
# ---------------------------------------------------------------------------
_data_dir = Path("data")
if _data_dir.exists():
    app.mount("/files", StaticFiles(directory=str(_data_dir)), name="files")
    logger.info("[main] Static files mounted at /files → %s", _data_dir.resolve())

# ---------------------------------------------------------------------------
# Include routers
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(compliance.router, prefix="/api/compliance", tags=["compliance"])
app.include_router(proposal.router, prefix="/api/proposal", tags=["proposal"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(opportunities.router, tags=["opportunities"])
app.include_router(proxy.router, tags=["proxy"])
app.include_router(pipeline.router, tags=["pipeline"])
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(jobs.router, tags=["jobs"])
app.include_router(communications.router, prefix="/api/communications", tags=["communications"])

logger.info("[main] All routers registered")


# ---------------------------------------------------------------------------
# Root & health endpoints
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "service": "MergenLite API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """Combined health check for Cloud Run / Docker / k8s."""
    db_status = check_db_health()
    return {
        "status": "healthy" if db_status.get("database") == "healthy" else "degraded",
        "service": "mergenlite-backend",
        **db_status,
    }


# ---------------------------------------------------------------------------
# Startup lifecycle
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """
    1. Run Alembic migrations
    2. Enable pgvector extension
    3. Send Telegram "system up" notification
    """
    logger.info("[startup] Application starting …")

    # 1. Migrations
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            logger.info("[startup] Alembic migrations applied successfully")
        else:
            logger.warning("[startup] Migration warning: %s", result.stderr)
    except Exception as exc:
        logger.warning("[startup] Migration error (continuing): %s", exc)

    # 2. pgvector
    init_pgvector()

    # 3. Startup notification
    from .services.notifications import notify_info
    await notify_info(
        "MergenLite v2.0 started successfully ✅",
        {
            "environment": settings.env,
            "database": settings.database_url[:40] + "...",
            "monitoring": "active" if settings.telegram_enabled else "disabled",
        },
    )

    logger.info("[startup] Application ready ✓")

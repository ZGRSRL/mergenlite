from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

# Load .env file from mergen/.env BEFORE importing anything else
try:
    from dotenv import load_dotenv
    # Get the project root (D:\Mergenlite)
    project_root = Path(__file__).parent.parent.parent.parent
    mergen_env_path = project_root / "mergen" / ".env"
    
    if mergen_env_path.exists():
        load_dotenv(mergen_env_path, override=True)
        print(f"[main.py] Loaded .env from: {mergen_env_path}")
    else:
        # Try alternative paths
        alt_paths = [
            project_root / ".env",
            Path("mergen/.env"),
            Path(".env"),
        ]
        for alt_path in alt_paths:
            if alt_path.exists():
                load_dotenv(alt_path, override=True)
                print(f"[main.py] Loaded .env from: {alt_path}")
                break
        else:
            print(f"[main.py] .env file not found. Tried: {mergen_env_path}")
except ImportError:
    print("[main.py] python-dotenv not installed")
except Exception as e:
    print(f"[main.py] Error loading .env: {e}")

# Import settings (non-blocking, just configuration)
try:
    from .config import settings
    print(f"[main.py] Settings loaded. Database host: {settings.postgres_host}")
except Exception as e:
    print(f"[main.py] WARNING: Failed to load settings: {e}")
    # Create a minimal settings object to prevent import errors
    class MinimalSettings:
        postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    settings = MinimalSettings()

# Import routes (lazy loading - database connections happen on request, not at startup)
try:
    from .routes import health, ingest, compliance, proposal, search, opportunities, proxy, pipeline, dashboard, jobs, communications
    print("[main.py] All routes imported successfully")
except Exception as e:
    print(f"[main.py] ERROR: Failed to import routes: {e}")
    import traceback
    traceback.print_exc()
    # Re-raise to fail fast
    raise

app = FastAPI(
    title="MergenLite API",
    description="MergenLite - RFQ/SOW Analysis and Proposal Generation API",
    version="1.0.0"
)

# Mount static files for downloads
data_dir = Path("data")
if data_dir.exists():
    app.mount("/files", StaticFiles(directory=str(data_dir)), name="files")
    print(f"[main.py] Static files mounted at /files from {data_dir.absolute()}")
else:
    print(f"[main.py] Warning: data directory not found at {data_dir.absolute()}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
try:
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
    print("[main.py] All routers included successfully")
except Exception as e:
    print(f"[main.py] ERROR: Failed to include routers: {e}")
    import traceback
    traceback.print_exc()
    raise


@app.get("/")
async def root():
    return {
        "message": "MergenLite API - RFQ/SOW Analysis and Proposal Generation",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy", "service": "mergenlite-backend"}


@app.on_event("startup")
async def startup_event():
    """Startup tasks - run migrations if needed"""
    print("[startup] Application starting...")
    try:
        # Run migrations on startup
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("[startup] Database migrations completed successfully")
        else:
            print(f"[startup] Migration warning: {result.stderr}")
    except Exception as e:
        print(f"[startup] Migration error (continuing anyway): {e}")
    print("[startup] Application startup complete")

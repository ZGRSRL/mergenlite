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

from .config import settings
from .routes import health, ingest, compliance, proposal, search, opportunities, proxy, pipeline, dashboard, jobs

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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
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


@app.get("/")
async def root():
    return {
        "message": "MergenLite API - RFQ/SOW Analysis and Proposal Generation",
        "version": "1.0.0",
        "docs": "/docs"
    }


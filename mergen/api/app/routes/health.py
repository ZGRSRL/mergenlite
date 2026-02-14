from fastapi import APIRouter
from datetime import datetime
from ..schemas import HealthResponse
from ..db import check_db_health

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint — includes DB connectivity."""
    db_status = check_db_health()
    return HealthResponse(
        status="ok" if db_status.get("database") == "healthy" else "degraded",
        timestamp=datetime.now(),
        version="2.0.0",
    )

"""
MergenLite — Global Exception Handler
======================================
Catches all unhandled exceptions in FastAPI and sends alerts.

Features:
  - Catches 500 errors (Internal Server Errors)
  - Sends Telegram notifications with full context
  - Logs detailed stack traces
  - Returns safe error responses to clients
  - Rate-limited to prevent spam during cascading failures
"""

import logging
import traceback
from typing import Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .services.notifications import send_alert_background

logger = logging.getLogger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global exception handler middleware.
    Catches any unhandled exception and:
      1. Logs the full stack trace
      2. Sends Telegram alert
      3. Returns a safe 500 response
    """

    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response

        except Exception as exc:
            # Log the full error
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}",
                exc_info=exc,
            )

            # Prepare context for alert
            context = {
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query) if request.url.query else None,
                "client": request.client.host if request.client else "unknown",
                "error_type": type(exc).__name__,
                "error": str(exc)[:200],  # Truncate long errors
            }

            # Send Telegram alert (non-blocking)
            send_alert_background(
                "ERROR",
                f"Unhandled exception in {request.method} {request.url.path}",
                context,
            )

            # Return safe error response
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "detail": "Internal server error",
                    "error_id": f"{type(exc).__name__}",
                    "path": request.url.path,
                },
            )


# ---------------------------------------------------------------------------
# Specific error handlers (optional — for more granular control)
# ---------------------------------------------------------------------------
async def database_error_handler(request: Request, exc: Exception):
    """Handle database connection errors specifically."""
    logger.error(f"Database error in {request.url.path}: {exc}")

    send_alert_background(
        "CRITICAL",
        "Database connection failed",
        {
            "path": request.url.path,
            "error": str(exc)[:200],
        },
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Database temporarily unavailable",
            "error_id": "DB_ERROR",
        },
    )


async def validation_error_handler(request: Request, exc: Exception):
    """Handle validation errors (422) — less critical, no alert."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": getattr(exc, "errors", lambda: [])(),
        },
    )

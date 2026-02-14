"""
MergenLite — FastAPI Dependencies
===================================
- get_db           : SQLAlchemy session dependency
- get_current_user : Simple username/password auth (2-user setup)
- require_admin    : Admin-only guard
"""

import os
import secrets
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from .db import get_db  # noqa: F401  (re-export for convenience)

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
security = HTTPBasic(auto_error=False)

# Users loaded from env vars — keep it simple for a 2-person team
_USERS: dict[str, dict] = {}


def _load_users():
    """
    Reads users from environment variables:
      AUTH_USER_1=admin:supersecret
      AUTH_USER_2=viewer:readonly
    Falls back to a default demo user when no AUTH_USER_* vars are set.
    """
    global _USERS
    _USERS = {}
    for key, value in os.environ.items():
        if key.startswith("AUTH_USER_") and ":" in value:
            username, password = value.split(":", 1)
            role = "admin" if "1" in key else "viewer"
            _USERS[username] = {"password": password, "role": role}
    # Fallback: if no users configured, allow a demo user
    if not _USERS:
        _USERS["admin"] = {"password": "mergenlite", "role": "admin"}
        _USERS["viewer"] = {"password": "viewer", "role": "viewer"}


_load_users()


# ---------------------------------------------------------------------------
# Current user dependency
# ---------------------------------------------------------------------------
def get_current_user(
    credentials: Optional[HTTPBasicCredentials] = Depends(security),
) -> dict:
    """
    Validate HTTP Basic credentials against the loaded user list.
    When no Authorization header is sent, fall back to demo_user
    (so existing un-authenticated calls keep working during migration).
    """
    if credentials is None:
        # No auth header — allow as demo user (remove this branch later)
        return {"user_id": "demo_user", "role": "admin"}

    user = _USERS.get(credentials.username)
    if user is None or not secrets.compare_digest(
        credentials.password.encode(), user["password"].encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"user_id": credentials.username, "role": user["role"]}


# ---------------------------------------------------------------------------
# Role guards
# ---------------------------------------------------------------------------
def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Raise 403 if the authenticated user is not an admin."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user

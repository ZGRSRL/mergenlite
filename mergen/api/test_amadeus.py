#!/usr/bin/env python
"""
Quick diagnostic script for Amadeus API integration.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

# Ensure app package import
CURRENT_DIR = Path(__file__).resolve().parent
APP_ROOT = CURRENT_DIR / "app"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT.parent))

from app.services.amadeus_client import amadeus_health_check


def main() -> int:
    status = amadeus_health_check()
    print("=" * 60)
    print("AMADEUS API HEALTH CHECK")
    print("=" * 60)
    print(json.dumps(status, indent=2))
    
    if status["status"] == "ok":
        print("\n[OK] Amadeus API is reachable and returned sample offers.")
        return 0
    if not status["configured"]:
        print("\n[WARN] Amadeus credentials are not configured.")
    elif not status["client_initialized"]:
        print("\n[WARN] Client could not be initialised. Check credentials/env.")
    else:
        print("\n[WARN] Amadeus API did not return offers. See status for detail.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

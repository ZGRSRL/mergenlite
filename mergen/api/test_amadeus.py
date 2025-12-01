#!/usr/bin/env python3
"""Test Amadeus API connectivity and credentials."""
import os
import sys
from pathlib import Path
import logging

# Add the parent directory to the Python path to import app modules
# In container, /app is the working directory, so we can import directly
# sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.amadeus_client import amadeus_health_check
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 60)
print("Amadeus API Health Check")
print("=" * 60)

print(f"\n[CONFIG] Environment: {settings.amadeus_env}")
print(f"[CONFIG] API Key: {settings.amadeus_api_key[:4]}***{settings.amadeus_api_key[-4:] if settings.amadeus_api_key else ''}")
print(f"[CONFIG] API Secret: {settings.amadeus_api_secret[:4]}***{settings.amadeus_api_secret[-4:] if settings.amadeus_api_secret else ''}")

print("\n[TEST] Running health check...")
health_status = amadeus_health_check()

print("\n[RESULT] Configured:", health_status["configured"])
print("[RESULT] Client Initialized:", health_status["client_initialized"])
print("[RESULT] Status:", health_status["status"])
print("[RESULT] City Code:", health_status["city_code"])
print("[RESULT] Offers Found:", health_status["offers_found"])

if health_status["status"] != "ok":
    logger.warning("Health check returned status: %s", health_status["status"])
    if health_status["status"] == "city_lookup_failed":
        logger.error("Amadeus city lookup failed for Washington: %s", health_status.get("error_details", "Unknown error"))
    elif health_status["status"] == "no_offers":
        logger.warning("No hotel offers found for test city. This might be expected for some test environments or specific dates.")
else:
    print("\n[OK] Amadeus API is reachable and returned offers for test city.")

print("\n" + "=" * 60)


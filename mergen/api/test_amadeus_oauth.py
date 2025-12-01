#!/usr/bin/env python3
"""Test Amadeus OAuth token retrieval manually."""
import os
import sys
import requests
from pathlib import Path

# Add parent directory to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "api"))

from app.config import settings

print("=" * 60)
print("Amadeus OAuth Token Test")
print("=" * 60)

print(f"\n[CONFIG] Environment: {settings.amadeus_env}")
print(f"[CONFIG] API Key: {settings.amadeus_api_key[:4]}***{settings.amadeus_api_key[-4:] if settings.amadeus_api_key else ''}")
print(f"[CONFIG] API Secret: {settings.amadeus_api_secret[:4]}***{settings.amadeus_api_secret[-4:] if settings.amadeus_api_secret else ''}")

if not settings.amadeus_api_key or not settings.amadeus_api_secret:
    print("\n[ERROR] API Key or Secret is missing!")
    sys.exit(1)

# Determine base URL based on environment
base_url = "https://test.api.amadeus.com" if settings.amadeus_env.lower() != "production" else "https://api.amadeus.com"
token_url = f"{base_url}/v1/security/oauth2/token"

print(f"\n[TEST] Requesting OAuth token from: {token_url}")

# Prepare request
data = {
    "grant_type": "client_credentials",
    "client_id": settings.amadeus_api_key,
    "client_secret": settings.amadeus_api_secret,
}

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
}

try:
    response = requests.post(token_url, data=data, headers=headers, timeout=10)
    print(f"[RESPONSE] Status Code: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        print("[OK] Token retrieved successfully!")
        print(f"[TOKEN] Type: {token_data.get('token_type')}")
        print(f"[TOKEN] Access Token: {token_data.get('access_token', '')[:20]}...")
        print(f"[TOKEN] Expires In: {token_data.get('expires_in')} seconds")
        print(f"[TOKEN] State: {token_data.get('state')}")
        print(f"[TOKEN] Username: {token_data.get('username')}")
        print(f"[TOKEN] Application: {token_data.get('application_name')}")
    else:
        print(f"[ERROR] Failed to get token")
        print(f"[ERROR] Response: {response.text}")
        try:
            error_data = response.json()
            print(f"[ERROR] Error details: {error_data}")
        except:
            pass
except requests.exceptions.RequestException as e:
    print(f"[ERROR] Request failed: {e}")

print("\n" + "=" * 60)


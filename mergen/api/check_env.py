#!/usr/bin/env python3
"""Check if .env file is being read correctly."""
import os
from dotenv import load_dotenv

# Load .env file - try multiple paths
load_dotenv('/app/.env')
if not os.getenv('AMADEUS_API_KEY'):
    # Try current directory
    load_dotenv('.env')
if not os.getenv('AMADEUS_API_KEY'):
    # Try parent directory
    load_dotenv('../.env')

print("=" * 60)
print("Environment Variables Check")
print("=" * 60)

api_key = os.getenv('AMADEUS_API_KEY')
api_secret = os.getenv('AMADEUS_API_SECRET')
env = os.getenv('AMADEUS_ENV')

print(f"\nAMADEUS_API_KEY: {api_key[:10] + '...' if api_key else 'NOT SET'}")
print(f"AMADEUS_API_SECRET: {api_secret[:10] + '...' if api_secret else 'NOT SET'}")
print(f"AMADEUS_ENV: {env}")

if api_key and api_secret:
    print("\n[OK] Amadeus credentials found in .env file")
else:
    print("\n[ERROR] Amadeus credentials NOT found in .env file")

print("=" * 60)


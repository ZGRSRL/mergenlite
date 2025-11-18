#!/usr/bin/env python3
"""Quick summary of .env configuration"""
import os
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent
    mergen_env_path = project_root / "mergen" / ".env"
    if mergen_env_path.exists():
        load_dotenv(mergen_env_path, override=True)
        print(f"[OK] Loaded .env from: {mergen_env_path}")
    else:
        load_dotenv(override=True)
        print(f"[WARNING] Using default .env location")
except ImportError:
    print("[WARNING] python-dotenv not installed")

print("\n" + "=" * 60)
print("ENVIRONMENT VARIABLES SUMMARY")
print("=" * 60)

# SAM API
sam_key = os.getenv('SAM_API_KEY', '')
print(f"\nSAM API:")
print(f"   SAM_API_KEY: {'[OK] Set' if sam_key else '[ERROR] Missing'} ({len(sam_key)} chars)")

# Database
db_host = os.getenv('POSTGRES_HOST', os.getenv('DB_HOST', 'localhost'))
db_user = os.getenv('POSTGRES_USER', os.getenv('DB_USER', 'postgres'))
db_name = os.getenv('POSTGRES_DB', os.getenv('DB_NAME', 'ZGR_AI'))
db_port = os.getenv('POSTGRES_PORT', os.getenv('DB_PORT', '5432'))

print(f"\nDatabase:")
print(f"   Host: {db_host} {'(will use localhost)' if db_host == 'db' else ''}")
print(f"   User: {db_user}")
print(f"   Database: {db_name}")
print(f"   Port: {db_port}")

print(f"\nRecommendations:")
if not sam_key:
    print(f"   - Add SAM_API_KEY to mergen/.env for SAM.gov API access")
if db_host == 'db':
    print(f"   - Change POSTGRES_HOST=db to POSTGRES_HOST=localhost for local dev")
print(f"   - Use /api/opportunities/sync to fetch opportunities from SAM.gov")


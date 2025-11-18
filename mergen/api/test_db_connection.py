#!/usr/bin/env python3
"""Test database connection"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.db import engine, get_db
from app.models import Opportunity
from sqlalchemy import text, func

print("=" * 60)
print("DATABASE CONNECTION TEST")
print("=" * 60)

print(f"\nDatabase Configuration:")
print(f"  Host: {settings.postgres_host}")
print(f"  Port: {settings.postgres_port}")
print(f"  Database: {settings.postgres_db}")
print(f"  User: {settings.postgres_user}")
print(f"  URL: postgresql://{settings.postgres_user}:***@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")

print(f"\nTesting connection...")
try:
    # Test 1: Raw connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"  [OK] PostgreSQL connection successful!")
        print(f"  Version: {version[:50]}...")
    
    # Test 2: ORM connection
    db = next(get_db())
    try:
        # Test query
        total = db.query(func.count(Opportunity.id)).scalar()
        print(f"  [OK] ORM connection successful!")
        print(f"  Total opportunities: {total}")
        
        # Test one record
        if total > 0:
            opp = db.query(Opportunity).first()
            print(f"  [OK] Sample record:")
            print(f"    ID: {opp.id}")
            print(f"    Title: {opp.title[:50]}...")
            print(f"    Notice ID: {opp.notice_id}")
            print(f"    Opportunity ID: {opp.opportunity_id}")
            print(f"    Posted Date: {opp.posted_date}")
            print(f"    Created At: {opp.created_at}")
            print(f"    Has raw_data: {bool(opp.raw_data)}")
            print(f"    Has cached_data: {bool(opp.cached_data)}")
    finally:
        db.close()
    
    print(f"\n[OK] All database tests passed!")
    
except Exception as e:
    print(f"\n[ERROR] Database connection failed!")
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


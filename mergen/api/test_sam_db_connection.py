#!/usr/bin/env python3
"""Test SAM API and Database connections"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 60)
print("SAM API & DATABASE CONNECTION TEST")
print("=" * 60)

# Test 1: Check .env file and SAM_API_KEY
print(f"\n1. Checking .env file and SAM_API_KEY...")
try:
    from dotenv import load_dotenv
    
    # Try to load .env from mergen/.env
    project_root = Path(__file__).parent.parent.parent
    mergen_env_path = project_root / "mergen" / ".env"
    
    if mergen_env_path.exists():
        load_dotenv(mergen_env_path, override=True)
        print(f"  [OK] .env file found: {mergen_env_path}")
    else:
        # Try alternative paths
        alt_paths = [project_root / ".env", Path("mergen/.env"), Path(".env")]
        for alt_path in alt_paths:
            if alt_path.exists():
                load_dotenv(alt_path, override=True)
                print(f"  [OK] .env file found: {alt_path}")
                break
        else:
            print(f"  [WARNING] .env file not found in expected locations")
    
    # Check SAM_API_KEY
    sam_api_key = os.getenv('SAM_API_KEY', '').strip()
    if sam_api_key:
        print(f"  [OK] SAM_API_KEY is set (length: {len(sam_api_key)})")
        print(f"       Key preview: {sam_api_key[:10]}...")
    else:
        print(f"  [ERROR] SAM_API_KEY is not set in .env file")
        print(f"          Please add SAM_API_KEY=your_key_here to mergen/.env")
    
except ImportError:
    print(f"  [ERROR] python-dotenv not installed")
except Exception as e:
    print(f"  [ERROR] Error loading .env: {e}")

# Test 2: Test SAMIntegration class
print(f"\n2. Testing SAMIntegration class...")
try:
    # Add project root to path for sam_integration
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    from sam_integration import SAMIntegration
    
    sam = SAMIntegration()
    if sam.api_key:
        print(f"  [OK] SAMIntegration initialized with API key")
        print(f"       API Key length: {len(sam.api_key)}")
        print(f"       Base URL: {sam.base_url}")
    else:
        print(f"  [WARNING] SAMIntegration initialized but API key is None")
        print(f"            SAM API calls will fail")
        
except ImportError as e:
    print(f"  [ERROR] Could not import SAMIntegration: {e}")
except Exception as e:
    print(f"  [ERROR] Error initializing SAMIntegration: {e}")

# Test 3: Check Database connection settings
print(f"\n3. Checking Database connection settings...")
try:
    from app.config import settings
    
    print(f"  Database Host: {settings.postgres_host}")
    print(f"  Database Port: {settings.postgres_port}")
    print(f"  Database Name: {settings.postgres_db}")
    print(f"  Database User: {settings.postgres_user}")
    print(f"  Database URL: postgresql://{settings.postgres_user}:***@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    
    # Check if host is 'db' (Docker) and suggest localhost for local dev
    if settings.postgres_host == 'db':
        print(f"  [INFO] Host is 'db' (Docker). For local dev, use 'localhost'")
    
except Exception as e:
    print(f"  [ERROR] Error loading database settings: {e}")

# Test 4: Test Database connection
print(f"\n4. Testing Database connection...")
try:
    from app.db import engine, get_db
    from app.models import Opportunity
    from sqlalchemy import text, func
    
    # Test raw connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"  [OK] PostgreSQL connection successful!")
        print(f"       Version: {version[:50]}...")
    
    # Test ORM connection and count
    db = next(get_db())
    try:
        # Try to count opportunities
        try:
            total = db.query(func.count(Opportunity.opportunity_id)).scalar() or 0
            print(f"  [OK] ORM connection successful!")
            print(f"       Total opportunities: {total}")
        except Exception as count_error:
            # Fallback: try id
            try:
                total = db.query(func.count(Opportunity.id)).scalar() or 0
                print(f"  [OK] ORM connection successful (using id)!")
                print(f"       Total opportunities: {total}")
            except Exception:
                print(f"  [WARNING] Could not count opportunities: {count_error}")
                total = 0
        
        # Test one record
        if total > 0:
            try:
                opp = db.query(Opportunity).first()
                print(f"  [OK] Sample record:")
                print(f"       Opportunity ID: {opp.opportunity_id}")
                print(f"       Notice ID: {opp.notice_id}")
                print(f"       Title: {opp.title[:50]}...")
            except Exception as sample_error:
                print(f"  [WARNING] Could not fetch sample record: {sample_error}")
        else:
            print(f"  [INFO] No opportunities in database yet")
            print(f"         Use /api/opportunities/sync to fetch from SAM.gov")
            
    finally:
        db.close()
    
except Exception as e:
    print(f"  [ERROR] Database connection failed!")
    print(f"         Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\n" + "=" * 60)
print("TEST COMPLETED")
print("=" * 60)

print(f"\nRecommendations:")
print(f"1. If SAM_API_KEY is missing, add it to mergen/.env")
print(f"2. If DB connection fails, check:")
print(f"   - PostgreSQL is running")
print(f"   - POSTGRES_HOST is 'localhost' for local dev (not 'db')")
print(f"   - POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB are correct")
print(f"3. To sync opportunities: POST /api/opportunities/sync")


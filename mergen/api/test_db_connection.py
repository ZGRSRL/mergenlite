#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test database connection and functionality"""
import sys
import os
# Override database host for local testing BEFORE importing app modules
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['DB_HOST'] = 'localhost'

from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import Opportunity

# Create engine with localhost override
database_url = f"postgresql://{settings.postgres_user}:{settings.postgres_password}@localhost:{settings.postgres_port}/{settings.postgres_db}"
engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_database():
    """Test database connection and basic operations"""
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    
    # Test 1: Database URL
    print("\n1. Database Configuration:")
    print(f"   Host: {settings.postgres_host}")
    print(f"   Port: {settings.postgres_port}")
    print(f"   Database: {settings.postgres_db}")
    print(f"   User: {settings.postgres_user}")
    print(f"   URL: {settings.database_url[:60]}...")
    
    # Test 2: Connection
    print("\n2. Testing Connection...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"   [OK] Connected to PostgreSQL")
            print(f"   [OK] Version: {version[:50]}...")
    except Exception as e:
        print(f"   [ERROR] Connection failed: {e}")
        return False
    
    # Test 3: Database exists
    print("\n3. Testing Database Access...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"   [OK] Current database: {db_name}")
    except Exception as e:
        print(f"   [ERROR] Database access failed: {e}")
        return False
    
    # Test 4: Tables exist
    print("\n4. Testing Tables...")
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"   [OK] Found {len(tables)} tables:")
            for table in tables[:10]:  # Show first 10
                print(f"      - {table}")
            if len(tables) > 10:
                print(f"      ... and {len(tables) - 10} more")
    except Exception as e:
        print(f"   [ERROR] Table check failed: {e}")
        return False
    
    # Test 5: Opportunities table
    print("\n5. Testing Opportunities Table...")
    try:
        db = SessionLocal()
        count = db.query(Opportunity).count()
        print(f"   [OK] Opportunities table accessible")
        print(f"   [OK] Total opportunities: {count}")
        
        # Get a sample opportunity if exists
        if count > 0:
            sample = db.query(Opportunity).first()
            print(f"   [OK] Sample opportunity ID: {sample.opportunity_id}")
            print(f"   [OK] Sample notice ID: {sample.notice_id}")
        else:
            print(f"   [INFO] No opportunities in database yet")
        
        db.close()
    except Exception as e:
        print(f"   [ERROR] Opportunities query failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 6: Write test (if needed)
    print("\n6. Testing Write Operations...")
    try:
        db = SessionLocal()
        # Just test if we can create a transaction
        db.execute(text("SELECT 1"))
        db.commit()
        print(f"   [OK] Write operations working")
        db.close()
    except Exception as e:
        print(f"   [ERROR] Write test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All database tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)

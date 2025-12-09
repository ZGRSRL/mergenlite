
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine
import logging

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))
try:
    import mergen.api.app
    sys.modules["app"] = mergen.api.app
except ImportError:
    pass

from mergen.api.app.config import settings
# Import Base via 'app' to match how models import it (hopefully)
try:
    from app.db import Base
except ImportError:
    # Fallback if patch didn't work immediately for some reason
    from mergen.api.app.db import Base

# Import models to ensure they are registered in Base.metadata
from mergen.api.app.models import db_models

def fix_missing_tables():
    print(f"Connecting to: {settings.database_url}")
    engine = create_engine(settings.database_url)
    
    print(f"Base.metadata tables: {list(Base.metadata.tables.keys())}")
    
    print("Check AI Analysis Results PK...")
    from sqlalchemy import text
    with engine.connect() as conn:
        # Check if analysis_id is PK
        result = conn.execute(text("SELECT a.attname FROM pg_index i JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey) WHERE i.indrelid = 'ai_analysis_results'::regclass AND i.indisprimary"))
        pk_col = result.scalar()
        print(f"Current PK column: {pk_col}")
        
        if pk_col == 'analysis_id':
            print("Fixing PK: Dropping analysis_id, setting id as PK...")
            conn.execute(text("ABORT")) # Ensure clean transaction start? No, just commit/begin.
            conn.commit() # Clear any transaction
            
            # Drop PK constraint
            conn.execute(text("ALTER TABLE ai_analysis_results DROP CONSTRAINT ai_analysis_results_pkey CASCADE"))
            # Drop analysis_id column
            conn.execute(text("ALTER TABLE ai_analysis_results DROP COLUMN analysis_id"))
            # Ensure id works
            # conn.execute(text("ALTER TABLE ai_analysis_results ADD PRIMARY KEY (id)")) # might fail if duplicates/null
            # Since ID was added as serial/autoincrement, it should be fine.
            # But let's check if 'id' is PK. If not, add it.
            conn.execute(text("ALTER TABLE ai_analysis_results ADD PRIMARY KEY (id)"))
            conn.commit()
            print("PK fixed.")
        elif pk_col == 'id':
            print("PK is already id.")

    print("Running Base.metadata.create_all()...")
    # This will create any tables that do not exist, based on the models
    Base.metadata.create_all(bind=engine)
    
    print("✅ create_all completed.")
    
    # Verify analysis_logs
    from sqlalchemy import inspect
    inspector = inspect(engine)
    if inspector.has_table("analysis_logs"):
        print("✅ analysis_logs table created.")
    else:
        print("❌ analysis_logs table STILL MISSING?")

if __name__ == "__main__":
    fix_missing_tables()

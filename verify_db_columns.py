
import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, inspect
import logging

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Fix 'app' import
try:
    import mergen.api.app
    sys.modules["app"] = mergen.api.app
except ImportError:
    pass

from mergen.api.app.config import settings

def verify_columns():
    print(f"Connecting to: {settings.database_url}")
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    
    tables = ["opportunities", "ai_analysis_results", "opportunity_attachments"]
    
    for table in tables:
        if not inspector.has_table(table):
            print(f"❌ Table '{table}' NOT found!")
            continue

        columns = inspector.get_columns(table)
        col_names = [c["name"] for c in columns]
        
        print(f"--- Table: {table} ---")
        print(sorted(col_names))
        
        if "id" not in col_names:
             print(f"❌ MISSING 'id' column in {table}")


if __name__ == "__main__":
    verify_columns()

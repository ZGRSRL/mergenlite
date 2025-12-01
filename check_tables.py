
import sys
import os
from sqlalchemy import create_engine, inspect, text

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from mergen.api.app.db import SQLALCHEMY_DATABASE_URL
except ImportError:
    SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ZGR_AI"

# Force ZGR_AI
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ZGR_AI"

def check_tables():
    print(f"Connecting to {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Found {len(tables)} tables: {tables}")
    
    target_tables = ["analysis_results", "ai_analysis_results", "agent_runs"]
    for table in target_tables:
        if table in tables:
            print(f"\nTable: {table}")
            columns = [(c['name'], str(c['type'])) for c in inspector.get_columns(table)]
            print(f"Columns: {columns}")
        else:
            print(f"\nTable '{table}' NOT FOUND.")

if __name__ == "__main__":
    check_tables()

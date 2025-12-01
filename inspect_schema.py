
import sys
from sqlalchemy import create_engine, text, inspect

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ZGR_AI"

def inspect_tables():
    print(f"Connecting to {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    
    for table in ["ai_analysis_results", "analysis_results"]:
        if inspector.has_table(table):
            print(f"\nTable: {table}")
            columns = inspector.get_columns(table)
            for c in columns:
                print(f"  {c['name']}: {c['type']}")
            
            with engine.connect() as conn:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  Row count: {count}")
        else:
            print(f"\nTable {table} NOT FOUND")

if __name__ == "__main__":
    inspect_tables()


import sys
from sqlalchemy import create_engine, text, inspect

SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ZGR_AI"

def fix_tables():
    print(f"Connecting to {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"Tables found: {tables}")
    
    with engine.connect() as connection:
        if "analysis_results" in tables:
            print("Found 'analysis_results'. Checking for 'ai_analysis_results'...")
            if "ai_analysis_results" not in tables:
                print("Renaming 'analysis_results' to 'ai_analysis_results'...")
                try:
                    connection.execute(text("ALTER TABLE analysis_results RENAME TO ai_analysis_results"))
                    connection.commit()
                    print("SUCCESS: Table renamed.")
                except Exception as e:
                    print(f"FAILED to rename table: {e}")
            else:
                print("Both tables exist. This is unexpected.")
        else:
            print("'analysis_results' NOT found.")
            
        if "ai_analysis_results" in tables:
            print("'ai_analysis_results' exists.")

if __name__ == "__main__":
    fix_tables()

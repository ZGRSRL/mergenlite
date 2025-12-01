
import sys
import os
import types
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Mock app.db module
m = types.ModuleType('app.db')
m.SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ZGR_AI"
sys.modules['app.db'] = m

# Mock app module
sys.modules['app'] = types.ModuleType('app')
sys.modules['app'].db = m

# Add project root to path for other imports if needed
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Now we can try to import models, but we might need to mock more if they import from app.*
# Let's try to import directly from the file path if possible, or just use raw SQL
# Raw SQL is safer and easier for this simple check.

def check_runs():
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/ZGR_AI")
    with engine.connect() as connection:
        print("--- Recent Agent Runs ---")
        result = connection.execute(text("SELECT id, run_type, status, started_at, error_message FROM agent_runs ORDER BY started_at DESC LIMIT 5"))
        for row in result:
            print(f"ID: {row[0]}, Type: {row[1]}, Status: {row[2]}, Started: {row[3]}, Error: {row[4]}")
            
        print("\n--- Recent Analysis Results ---")
        result = connection.execute(text("SELECT id, analysis_type, status, created_at FROM ai_analysis_results ORDER BY created_at DESC LIMIT 5"))
        for row in result:
            print(f"ID: {row[0]}, Type: {row[1]}, Status: {row[2]}, Created: {row[3]}")

if __name__ == "__main__":
    check_runs()

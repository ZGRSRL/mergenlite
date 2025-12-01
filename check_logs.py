
import sys
import os
import types
from sqlalchemy import create_engine, text

# Mock app.db module
m = types.ModuleType('app.db')
m.SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ZGR_AI"
sys.modules['app.db'] = m

# Mock app module
sys.modules['app'] = types.ModuleType('app')
sys.modules['app'].db = m

def check_logs():
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/ZGR_AI")
    with engine.connect() as connection:
        print("--- Analysis Logs for Run 1 ---")
        # Assuming analysis_result_id corresponds to the run or we can join. 
        # Let's just check all recent logs.
        result = connection.execute(text("SELECT level, message, step, created_at FROM analysis_logs ORDER BY created_at DESC LIMIT 10"))
        for row in result:
            print(f"[{row[3]}] {row[0]}: {row[1]} (Step: {row[2]})")

if __name__ == "__main__":
    check_logs()

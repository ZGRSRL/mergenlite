
import sys
import os
from sqlalchemy import create_engine, text

# Add api folder to path so 'app' can be imported
project_root = os.path.dirname(os.path.abspath(__file__))
api_path = os.path.join(project_root, "mergen", "api")
sys.path.insert(0, api_path)

# We need to set environment variables for config to work
os.environ["DATABASE_URL"] = "postgresql://postgres:postgres@localhost:5432/ZGR_AI"
os.environ["ENV"] = "dev"

from app.models.db_models import Base, AIAnalysisResult
from app.config import settings

SQLALCHEMY_DATABASE_URL = settings.database_url

def recreate_table():
    print(f"Connecting to {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    print("Dropping 'ai_analysis_results' and 'analysis_results'...")
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS ai_analysis_results CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS analysis_results CASCADE"))
        conn.commit()
        
    print("Creating 'ai_analysis_results'...")
    # Create only the specific table
    AIAnalysisResult.__table__.create(engine)
    print("SUCCESS: Table recreated.")

if __name__ == "__main__":
    recreate_table()

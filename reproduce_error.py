
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Mock config to avoid import errors
import types
sys.modules['mergen.api.app.config'] = types.ModuleType('config')
sys.modules['mergen.api.app.config'].settings = types.SimpleNamespace(database_url="postgresql://postgres:postgres@localhost:5432/ZGR_AI", env="dev")

from mergen.api.app.models.db_models import AIAnalysisResult
from mergen.api.app.db import SQLALCHEMY_DATABASE_URL

# Override DB URL to ZGR_AI
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ZGR_AI"

def reproduce():
    print(f"Connecting to {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    opportunity_id = 277
    limit = 10
    
    print(f"Querying AIAnalysisResult for opportunity_id={opportunity_id} with limit={limit}")
    try:
        results = (
            db.query(AIAnalysisResult)
            .filter(AIAnalysisResult.opportunity_id == opportunity_id)
            .order_by(AIAnalysisResult.created_at.desc())
            .limit(limit)
            .all()
        )
        print(f"Success! Found {len(results)} results.")
    except Exception as e:
        print(f"Caught exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    reproduce()

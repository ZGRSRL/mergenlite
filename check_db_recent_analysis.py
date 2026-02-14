import sys
import os
sys.path.append(os.getcwd())
from backend_utils import get_db_session
from mergenlite_models import AIAnalysisResult
from sqlalchemy import desc

def check_recent_db():
    db = get_db_session()
    if not db:
        print("No DB connection")
        return

    results = db.query(AIAnalysisResult).order_by(desc(AIAnalysisResult.created_at)).limit(5).all()
    print(f"Found {len(results)} recent analysis results:")
    for res in results:
        print(f"ID: {res.id} | Type: {res.analysis_type} | Status: {res.result.get('status') if res.result else 'N/A'} | OppID: {res.opportunity_id}")
    db.close()

if __name__ == "__main__":
    check_recent_db()


import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.schema import MetaData

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))
try:
    import mergen.api.app
    sys.modules["app"] = mergen.api.app
except ImportError:
    pass

from mergen.api.app.config import settings

def verify_constraints():
    print(f"Connecting to: {settings.database_url}")
    engine = create_engine(settings.database_url)
    inspector = inspect(engine)
    
    # 1. Check Opportunities PK
    pk = inspector.get_pk_constraint("opportunities")
    print(f"Opportunities PK: {pk}")
    
    # Check AI PK
    ai_pk = inspector.get_pk_constraint("ai_analysis_results")
    print(f"AIAnalysisResults PK: {ai_pk}")

    # 2. Check AI Analysis Results Constraints
    fks = inspector.get_foreign_keys("ai_analysis_results")
    print(f"AI Analysis Results FKs: {fks}")
    
    # 3. Check table columns types
    opp_cols = inspector.get_columns("opportunities")
    id_col = next((c for c in opp_cols if c["name"] == "id"), None)
    print(f"Opportunities.id type: {id_col['type']}")
    
    ar_cols = inspector.get_columns("ai_analysis_results")
    ar_opp_id = next((c for c in ar_cols if c["name"] == "opportunity_id"), None)
    print(f"AIAnalysisResult.opportunity_id type: {ar_opp_id['type']}")

if __name__ == "__main__":
    verify_constraints()

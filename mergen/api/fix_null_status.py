"""Quick fix: fill NULL status in opportunities before migration."""
import sys
sys.path.insert(0, ".")
from app.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(
        text("UPDATE opportunities SET status = 'new' WHERE status IS NULL")
    )
    conn.commit()
    print(f"Updated {result.rowcount} rows with status='new'")

    # Also fix ai_analysis_results nulls
    r2 = conn.execute(
        text("UPDATE ai_analysis_results SET analysis_type = 'sow_analysis' WHERE analysis_type IS NULL")
    )
    r3 = conn.execute(
        text("UPDATE ai_analysis_results SET status = 'pending' WHERE status IS NULL")
    )
    conn.commit()
    print(f"Fixed analysis_type: {r2.rowcount}, status: {r3.rowcount}")

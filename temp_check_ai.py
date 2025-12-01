from mergen.api.app.db import SessionLocal
from mergen.api.app.models import AIAnalysisResult
session = SessionLocal()
try:
    results = session.query(AIAnalysisResult).order_by(AIAnalysisResult.id.desc()).limit(3).all()
    for r in results:
        print(r.id, r.analysis_type, getattr(r, "status", None), r.pdf_path)
finally:
    session.close()

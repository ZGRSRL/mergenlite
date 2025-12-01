#!/usr/bin/env python3
"""Check if email was sent for Hotel Match 282."""
from app.db import SessionLocal
from app.models import AnalysisLog

db = SessionLocal()
logs = db.query(AnalysisLog).filter(
    AnalysisLog.analysis_result_id == 282
).filter(
    AnalysisLog.message.ilike('%email%')
).order_by(AnalysisLog.id.desc()).limit(5).all()

print("📧 Email Logları - Hotel Match #282")
print("=" * 50)

if logs:
    print(f"✅ {len(logs)} email log bulundu:")
    for log in logs:
        print(f"   - {log.message[:200]}")
else:
    print("❌ Email log bulunamadı")

db.close()


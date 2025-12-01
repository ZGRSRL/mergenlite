#!/usr/bin/env python3
"""Quick check of pipeline status."""
from app.db import SessionLocal
from app.models import AIAnalysisResult
from datetime import datetime

db = SessionLocal()

# Get latest results for opportunity 6
results = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 6
).order_by(AIAnalysisResult.created_at.desc()).limit(5).all()

print("=" * 70)
print("📊 PIPELINE STATUS - Opportunity #6")
print("=" * 70)
print()

for r in results:
    age = (datetime.utcnow() - r.created_at.replace(tzinfo=None)).total_seconds() / 60
    print(f"ID: {r.id} | Type: {r.analysis_type:15} | Status: {r.status:12} | Age: {age:.1f} min")
    
    if r.analysis_type == 'hotel_match' and r.status == 'completed':
        import json
        result_json = r.result_json if isinstance(r.result_json, dict) else json.loads(r.result_json) if r.result_json else {}
        hotels = result_json.get('hotels', [])
        print(f"   → Hotels found: {len(hotels)}")
        if result_json.get('fallback_used'):
            print(f"   → ⚠️ Fallback mechanism was used")
    
    if r.status == 'running':
        print(f"   → ⏳ Still running...")

print()
print("=" * 70)

db.close()


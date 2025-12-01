#!/usr/bin/env python3
"""Check if hotel match was auto-triggered for SOW 279."""
from app.db import SessionLocal
from app.models import AIAnalysisResult
from datetime import datetime, timedelta

db = SessionLocal()

# Get SOW 279
sow = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 279).first()
if sow:
    print(f"SOW 279: Status={sow.status}, Created={sow.created_at}")
    
    # Check hotel matches created after SOW 279
    sow_time = sow.created_at
    hotel_matches = db.query(AIAnalysisResult).filter(
        AIAnalysisResult.opportunity_id == 6,
        AIAnalysisResult.analysis_type == 'hotel_match',
        AIAnalysisResult.created_at >= sow_time
    ).order_by(AIAnalysisResult.created_at.desc()).all()
    
    print(f"\nHotel Matches created after SOW 279: {len(hotel_matches)}")
    for hm in hotel_matches:
        print(f"  - ID: {hm.id}, Status: {hm.status}, Created: {hm.created_at}")
        if hm.result_json:
            import json
            result = hm.result_json if isinstance(hm.result_json, dict) else json.loads(hm.result_json)
            hotels = result.get('hotels', [])
            fallback = result.get('fallback_used', False)
            print(f"    Hotels: {len(hotels)}, Fallback: {fallback}")
else:
    print("SOW 279 not found")

db.close()


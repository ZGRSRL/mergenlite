#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()
try:
    sow = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 217).first()
    if not sow:
        print("❌ SOW 217 bulunamadı!")
        exit(1)
    
    print(f"SOW 217 Status: {sow.status}")
    print(f"Has result_json: {bool(sow.result_json)}")
    
    if sow.result_json:
        data = sow.result_json
        if isinstance(data, str):
            data = json.loads(data) if data else {}
        
        sow_analysis = data.get('sow_analysis', {})
        locations = sow_analysis.get('Locations', [])
        print(f"Locations count: {len(locations) if locations else 0}")
        if locations and len(locations) > 0:
            print(f"First location: {locations[0].get('city', 'N/A')}")
finally:
    db.close()


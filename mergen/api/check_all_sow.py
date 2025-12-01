#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()
try:
    sows = db.query(AIAnalysisResult).filter(
        AIAnalysisResult.opportunity_id == 3,
        AIAnalysisResult.analysis_type.in_(['sow', 'sow_draft']),
        AIAnalysisResult.status == 'completed'
    ).order_by(AIAnalysisResult.created_at.desc()).all()
    
    print('Completed SOW Analyses:')
    for s in sows[:5]:
        locations_count = 0
        if s.result_json:
            data = s.result_json if isinstance(s.result_json, dict) else json.loads(s.result_json) if s.result_json else {}
            sow_analysis = data.get('sow_analysis', {})
            locations = sow_analysis.get('Locations', [])
            locations_count = len(locations) if locations else 0
        print(f'  ID {s.id}: {s.created_at}, Locations: {locations_count}')
finally:
    db.close()


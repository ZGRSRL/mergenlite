#!/usr/bin/env python3
"""Check SOW Analysis 280 results."""
from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 280).first()

if result and result.result_json:
    data = result.result_json if isinstance(result.result_json, dict) else json.loads(result.result_json) if result.result_json else {}
    sow = data.get('sow_analysis', {})
    locs = sow.get('Locations', [])
    event_details = sow.get('EventDetails', {})
    
    print(f"Locations count: {len(locs)}")
    print(f"EventDetails start_date: {event_details.get('start_date', 'N/A')}")
    print(f"EventDetails end_date: {event_details.get('end_date', 'N/A')}")
    print(f"EventDetails location: {event_details.get('location', 'N/A')}")
    
    if locs:
        print(f"\nFirst location: {locs[0]}")
    else:
        print("\n⚠️ No locations found in SOW analysis!")
        
    # Check document analysis
    doc_analysis = data.get('document_analysis', {})
    print(f"\nDocument Analysis:")
    print(f"  Total words: {doc_analysis.get('total_word_count', 'N/A')}")
    print(f"  Total chars: {doc_analysis.get('total_text_length', 'N/A')}")
    print(f"  Tables: {doc_analysis.get('total_tables', 'N/A')}")

db.close()


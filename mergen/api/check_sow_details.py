from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Check analysis 231
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 231).first()
if result and result.result_json:
    data = result.result_json
    if isinstance(data, str):
        data = json.loads(data)
    
    # Check document analysis
    doc_analysis = data.get('document_analysis', {})
    if doc_analysis:
        print("Document Analysis:")
        print(f"  Total documents: {len(doc_analysis.get('documents', []))}")
        for i, doc in enumerate(doc_analysis.get('documents', []), 1):
            text_len = doc.get('text_length', 0)
            word_count = doc.get('word_count', 0)
            print(f"  Doc {i}: {text_len} chars, {word_count} words")
            if text_len < 100:
                print(f"    ⚠️ WARNING: Very short text! Preview: {doc.get('extracted_text', '')[:100]}")
    
    # Check SOW analysis
    sow = data.get('sow_analysis', {})
    if sow:
        print(f"\nSOW Analysis:")
        print(f"  Event Name: {sow.get('EventDetails', {}).get('event_name', 'N/A') if isinstance(sow.get('EventDetails'), dict) else 'N/A'}")
        locations = sow.get('Locations', [])
        print(f"  Locations: {len(locations)}")
        if len(locations) == 0:
            print("  ❌ No locations extracted!")
            # Check if there's any location data elsewhere
            event_details = sow.get('EventDetails', {})
            if isinstance(event_details, dict):
                event_locs = event_details.get('locations', [])
                if event_locs:
                    print(f"  Found locations in EventDetails: {len(event_locs)}")
    else:
        print("❌ No sow_analysis in result")

db.close()


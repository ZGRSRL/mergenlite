from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Analysis 246'yı kontrol et
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 246).first()

if result:
    print(f"--- ANALİZ 246 DETAYLI RAPORU ---")
    print(f"Status: {result.status}")
    print(f"Type: {result.analysis_type}")
    print(f"PDF: {result.pdf_path}")
    
    if result.result_json:
        data = result.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        # Document analysis
        doc_analysis = data.get('document_analysis', {})
        print(f"\n📊 Document Analysis:")
        print(f"   Words: {doc_analysis.get('total_word_count', 0):,}")
        print(f"   Chars: {doc_analysis.get('total_text_length', 0):,}")
        print(f"   Tables: {doc_analysis.get('total_tables', 0)}")
        print(f"   Documents: {doc_analysis.get('documents_analyzed', 0)}")
        
        # SOW Analysis
        sow_analysis = data.get('sow_analysis', {})
        if sow_analysis:
            print(f"\n✅ SOW Analysis:")
            locations = sow_analysis.get('Locations', [])
            print(f"   Locations: {len(locations)}")
            
            event_details = sow_analysis.get('EventDetails', {})
            print(f"   Event Name: {event_details.get('event_name', 'N/A')}")
        else:
            print(f"\n❌ SOW Analysis yok!")
        
        # Check for errors
        if data.get('error'):
            print(f"\n❌ Error: {data.get('error')}")
        
        # Notes
        notes = data.get('notes', '')
        if notes:
            print(f"\n📝 Notes: {notes[:200]}")
    else:
        print("❌ Result JSON boş!")

db.close()


from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Analysis 250'yi kontrol et
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 250).first()

if result:
    print("=" * 70)
    print("📊 ANALİZ 250 - PDF İÇERİK KONTROLÜ")
    print("=" * 70)
    print()
    
    if result.result_json:
        data = result.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        # SOW Analysis
        sow_analysis = data.get('sow_analysis', {})
        if sow_analysis:
            event = sow_analysis.get('EventDetails', {})
            print("📅 Event Details (SOW Analysis'ten):")
            print(f"   Event Name: {event.get('event_name', 'N/A')}")
            print(f"   Start Date: {event.get('start_date', 'N/A')}")
            print(f"   End Date: {event.get('end_date', 'N/A')}")
            print(f"   Duration: {event.get('duration_days', 'N/A')}")
            print(f"   Submission Due: {event.get('submission_due', 'N/A')}")
            
            locations = event.get('locations', [])
            if locations:
                print(f"   Locations Array: {len(locations)}")
                print(f"   First Location: {locations[0] if isinstance(locations[0], dict) else locations[0]}")
            else:
                print(f"   Locations: []")
            
            print()
            
            # Check what's missing
            print("⚠️ Eksik Veriler:")
            missing = []
            if not event.get('start_date') or event.get('start_date') in ['N/A', None]:
                missing.append("Start Date")
            if not event.get('end_date') or event.get('end_date') in ['N/A', None]:
                missing.append("End Date")
            if not event.get('submission_due') or event.get('submission_due') in ['N/A', None]:
                missing.append("Submission Due")
            
            if missing:
                print(f"   {', '.join(missing)}")
            else:
                print("   Tüm Event Details alanları dolu ✅")
            
            # Document Analysis
            doc_analysis = data.get('document_analysis', {})
            print(f"\n📄 Document Analysis:")
            print(f"   Words: {doc_analysis.get('total_word_count', 0):,}")
            print(f"   Chars: {doc_analysis.get('total_text_length', 0):,}")
            print(f"   Tables: {doc_analysis.get('total_tables', 0)}")
            
            # Check combined text
            combined_preview = doc_analysis.get('combined_text_preview', '')
            if combined_preview:
                print(f"\n   Combined Text Preview (ilk 300 karakter):")
                print(f"   {combined_preview[:300]}...")
        else:
            print("❌ SOW Analysis yok!")

db.close()


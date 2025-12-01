from app.db import SessionLocal
from app.models import AIAnalysisResult
import json
from pathlib import Path

db = SessionLocal()

# Analysis 248'i detaylı kontrol et
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 248).first()

if result:
    print("=" * 70)
    print("📊 ANALİZ 248 DETAYLI İNCELEME")
    print("=" * 70)
    print()
    
    if result.result_json:
        data = result.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        # Document Analysis
        doc_analysis = data.get('document_analysis', {})
        print("📄 DOCUMENT ANALYSIS:")
        print(f"   Documents: {doc_analysis.get('documents_analyzed', 0)}")
        print(f"   Words: {doc_analysis.get('total_word_count', 0):,}")
        print(f"   Chars: {doc_analysis.get('total_text_length', 0):,}")
        print(f"   Tables: {doc_analysis.get('total_tables', 0)}")
        
        # Check individual documents
        documents = doc_analysis.get('documents', [])
        if documents:
            print(f"\n   📋 Individual Documents:")
            for i, doc in enumerate(documents, 1):
                print(f"      {i}. {doc.get('name', 'N/A')}")
                print(f"         Words: {doc.get('word_count', 0):,}")
                print(f"         Chars: {doc.get('text_length', 0):,}")
                print(f"         Tables: {doc.get('tables', 0)}")
        
        # Combined text preview
        combined_preview = doc_analysis.get('combined_text_preview', '')
        if combined_preview:
            print(f"\n   📝 Combined Text Preview (ilk 500 karakter):")
            print(f"      {combined_preview[:500]}...")
        
        # SOW Analysis
        sow_analysis = data.get('sow_analysis', {})
        print(f"\n" + "=" * 70)
        print("📋 SOW ANALYSIS:")
        print("=" * 70)
        
        if sow_analysis:
            # Event Details
            event = sow_analysis.get('EventDetails', {})
            print(f"\n📅 Event Details:")
            print(f"   Event Name: {event.get('event_name', 'N/A')}")
            print(f"   Start Date: {event.get('start_date', 'N/A')}")
            print(f"   End Date: {event.get('end_date', 'N/A')}")
            print(f"   Duration: {event.get('duration_days', 'N/A')}")
            print(f"   Location: {event.get('locations', [])}")
            print(f"   Submission Due: {event.get('submission_due', 'N/A')}")
            
            # Locations
            locations = sow_analysis.get('Locations', [])
            print(f"\n🏙️ Locations: {len(locations)}")
            for loc in locations:
                print(f"   - {loc}")
            
            # Lodging Requirements
            lodging = sow_analysis.get('LodgingRequirements', {})
            print(f"\n🛏️ Lodging Requirements:")
            print(f"   Rooms Min: {lodging.get('rooms_per_city_min', 'N/A')}")
            print(f"   Rooms Max: {lodging.get('rooms_per_city_max', 'N/A')}")
            print(f"   Max Stay Days: {lodging.get('max_stay_days_per_city', 'N/A')}")
            
            # Period of Performance
            pop = sow_analysis.get('PeriodOfPerformance', {})
            print(f"\n📆 Period of Performance:")
            print(f"   Start: {pop.get('start_date', 'N/A')}")
            print(f"   End: {pop.get('end_date', 'N/A')}")
            
            # Check for missing data
            print(f"\n⚠️ Eksik Veriler:")
            missing = []
            if not event.get('start_date') or event.get('start_date') == 'N/A':
                missing.append("Event Start Date")
            if not event.get('end_date') or event.get('end_date') == 'N/A':
                missing.append("Event End Date")
            if not event.get('submission_due') or event.get('submission_due') == 'N/A':
                missing.append("Submission Due Date")
            
            if missing:
                print(f"   {', '.join(missing)}")
            else:
                print(f"   Eksik veri yok")
        else:
            print("❌ SOW Analysis yok!")
    
    # Check PDF size
    if result.pdf_path:
        pdf = Path(result.pdf_path)
        if pdf.exists():
            print(f"\n📄 PDF Size: {pdf.stat().st_size:,} bytes")
        else:
            print(f"\n❌ PDF bulunamadı: {result.pdf_path}")

db.close()


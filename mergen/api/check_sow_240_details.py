from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# SOW 240'ı detaylı kontrol et
sow = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 240).first()

if sow and sow.result_json:
    data = sow.result_json
    if isinstance(data, str):
        data = json.loads(data)
    
    print("=" * 60)
    print("SOW ANALİZİ 240 - DETAYLI KONTROL")
    print("=" * 60)
    
    # Document analysis
    doc_analysis = data.get('document_analysis', {})
    print(f"\n📄 Document Analysis:")
    print(f"   - Text length: {doc_analysis.get('total_text_length', 0):,}")
    print(f"   - Word count: {doc_analysis.get('total_word_count', 0):,}")
    print(f"   - Tables: {doc_analysis.get('total_tables', 0)}")
    
    # Combined text preview - tablolar var mı?
    combined_preview = doc_analysis.get('combined_text_preview', '')
    if '[TABLE' in combined_preview:
        print(f"\n   ✅ Tablolar metin içinde var!")
        # İlk tabloyu bul
        table_start = combined_preview.find('[TABLE')
        if table_start >= 0:
            table_end = combined_preview.find('\n\n', table_start + 100)
            if table_end > table_start:
                print(f"   İlk tablo önizlemesi:")
                print(f"   {combined_preview[table_start:table_start+500]}")
    else:
        print(f"\n   ⚠️ Tablolar metin önizlemesinde görünmüyor")
    
    # SOW Analysis
    sow_analysis = data.get('sow_analysis', {})
    if sow_analysis:
        print(f"\n🤖 SOW Analysis (AutoGen çıktısı):")
        
        # Locations kontrolü
        locations = sow_analysis.get('Locations', [])
        print(f"   - Locations array: {len(locations)}")
        if locations:
            print(f"   ✅ Locations bulundu!")
            for i, loc in enumerate(locations[:3], 1):
                print(f"      {i}. City: {loc.get('city', 'N/A')}, Stadium: {loc.get('stadium', 'N/A')}")
        else:
            print(f"   ❌ Locations array boş!")
        
        # Table extraction failed flag
        table_failed = sow_analysis.get('table_extraction_failed', False)
        print(f"   - table_extraction_failed: {table_failed}")
        
        # Data quality issues
        quality_issues = sow_analysis.get('data_quality_issues', [])
        if quality_issues:
            print(f"   - Data quality issues: {len(quality_issues)}")
            for issue in quality_issues[:3]:
                print(f"      • {issue}")
        
        # Event Details
        event = sow_analysis.get('EventDetails', {})
        if event:
            print(f"\n   📋 Event Details:")
            print(f"      - Event Name: {event.get('event_name', 'N/A')}")
            print(f"      - Agency: {event.get('agency', 'N/A')}")
    else:
        print(f"\n❌ SOW Analysis yok!")

db.close()


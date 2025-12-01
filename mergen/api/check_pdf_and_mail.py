from app.db import SessionLocal
from app.models import AIAnalysisResult
import json
from pathlib import Path

db = SessionLocal()

# En son SOW analizini kontrol et
sow = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3,
    AIAnalysisResult.analysis_type.in_(['sow', 'sow_draft']),
    AIAnalysisResult.status == 'completed'
).order_by(AIAnalysisResult.created_at.desc()).first()

if sow:
    print(f"--- SOW ANALİZİ PDF VE MAİL KONTROLÜ ---")
    print(f"Analysis ID: {sow.id}")
    print(f"Status: {sow.status}")
    print(f"Created: {sow.created_at}")
    
    # PDF kontrolü
    print(f"\n📄 PDF Kontrolü:")
    if sow.pdf_path:
        pdf_path = Path(sow.pdf_path)
        print(f"   - PDF Path: {sow.pdf_path}")
        print(f"   - PDF Exists: {pdf_path.exists()}")
        if pdf_path.exists():
            size = pdf_path.stat().st_size
            print(f"   - PDF Size: {size:,} bytes")
        else:
            print(f"   ❌ PDF dosyası bulunamadı!")
    else:
        print(f"   ❌ PDF path yok!")
    
    # JSON kontrolü
    if sow.json_path:
        json_path = Path(sow.json_path)
        print(f"\n📋 JSON Kontrolü:")
        print(f"   - JSON Path: {sow.json_path}")
        print(f"   - JSON Exists: {json_path.exists()}")
    
    # Result JSON kontrolü
    if sow.result_json:
        data = sow.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        # Notes kontrolü - mail gönderildi mi?
        notes = data.get('notes', '')
        if 'email' in notes.lower() or 'mail' in notes.lower():
            print(f"\n📧 Mail bilgisi notes'da var")
        else:
            print(f"\n⚠️ Mail bilgisi notes'da yok")
        
        # Document analysis
        doc_analysis = data.get('document_analysis', {})
        print(f"\n📊 Document Analysis:")
        print(f"   - Words: {doc_analysis.get('total_word_count', 0):,}")
        print(f"   - Tables: {doc_analysis.get('total_tables', 0)}")
        
        # SOW Analysis
        sow_analysis = data.get('sow_analysis', {})
        if sow_analysis:
            locations = sow_analysis.get('Locations', [])
            print(f"   - Locations: {len(locations)}")
else:
    print("SOW analizi bulunamadı")

# Mail servisi kontrolü
print(f"\n" + "=" * 60)
print("MAİL SERVİSİ KONTROLÜ")
print("=" * 60)

try:
    from app.services.mail_service import send_analysis_email
    print("✅ Mail servisi import edilebildi")
except ImportError as e:
    print(f"❌ Mail servisi import edilemedi: {e}")

db.close()


from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

res = db.query(AIAnalysisResult).order_by(AIAnalysisResult.created_at.desc()).first()
print(f'--- EN SON ANALİZ RAPORU ---')
print(f'Analysis ID: {res.id}, Status: {res.status}')

if res.result_json:
    data = res.result_json
    if isinstance(data, str):
        data = json.loads(data)
    
    doc = data.get('document_analysis', {})
    chars = doc.get('total_text_length', 0)
    words = doc.get('total_word_count', 0)
    tables = doc.get('total_tables', 0)
    
    print(f'\n📊 İstatistikler:')
    print(f'   - Karakter: {chars:,}')
    print(f'   - Kelime: {words:,}')
    print(f'   - Tablo: {tables}')
    
    sow = data.get('sow_analysis', {})
    if sow and isinstance(sow, dict):
        locs = sow.get('Locations', [])
        print(f'\n✅ SOW ÇIKTISI:')
        print(f'   - Tespit Edilen Şehir Sayısı: {len(locs)}')
        if locs:
            print(f'   - İlk Şehir: {locs[0].get("city", "N/A")}')
            if len(locs) >= 11:
                print(f'   🎉 BAŞARILI! 11 şehir bulundu!')
    else:
        print(f'\n❌ SOW analizi yok veya boş')

db.close()


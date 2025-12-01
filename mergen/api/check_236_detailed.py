from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# ID 236 Sonucunu Çek
res = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 236).first()

print(f'--- ANALİZ 236 RAPORU ---')
if not res:
    print('❌ Analiz 236 bulunamadı!')
    db.close()
    exit()

print(f'Durum: {res.status}')

if res.result_json:
    data = res.result_json
    if isinstance(data, str):
        data = json.loads(data)
    
    # 1. Doküman İstatistikleri
    doc = data.get('document_analysis', {})
    chars = doc.get('total_text_length', 0)
    words = doc.get('total_word_count', 0)
    tables = doc.get('total_tables', 0)
    
    print(f'\n📊 İstatistikler:')
    print(f'   - Karakter: {chars:,}')
    print(f'   - Kelime: {words:,}')
    print(f'   - Tablo: {tables}')
    
    # 2. Kritik Veri: Şehirler
    sow = data.get('sow_analysis')
    if sow:
        if isinstance(sow, dict):
            locs = sow.get('Locations', [])
            print(f'\n✅ SOW ÇIKTISI:')
            print(f'   - Tespit Edilen Şehir Sayısı: {len(locs)}')
            if locs:
                print(f'   - İlk Şehir: {locs[0].get("city", "N/A") if isinstance(locs[0], dict) else locs[0]}')
                if len(locs) > 1:
                    print(f'   - İkinci Şehir: {locs[1].get("city", "N/A") if isinstance(locs[1], dict) else locs[1]}')
                if len(locs) >= 11:
                    print(f'   🎉 BAŞARILI! 11 şehir bulundu!')
            
            # Event Details kontrolü
            event_details = sow.get('EventDetails', {})
            if event_details:
                print(f'\n📋 Event Details:')
                print(f'   - Event Name: {event_details.get("event_name", "N/A")}')
                print(f'   - Agency: {event_details.get("agency", "N/A")}')
        else:
            print(f'\n⚠️ SOW analizi dict değil, tip: {type(sow)}')
    else:
        print('\n❌ SOW Analizi (sow_analysis) anahtarı yok.')
        print(f'   Mevcut anahtarlar: {list(data.keys())}')
else:
    print('⚠️ Sonuç JSON boş.')

db.close()


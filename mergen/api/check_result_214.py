#!/usr/bin/env python3
"""Check Hotel Match result ID 214."""
import sys
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()
try:
    # ID 214 (Son başlatılan işlem)
    res = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 214).first()
    
    if not res:
        print("❌ ID 214 bulunamadı!")
        exit(1)
    
    print(f'--- ANALİZ SONUCU (ID: 214) ---')
    print(f'Status: {res.status}')
    print(f'Analysis Type: {res.analysis_type}')
    print(f'Created: {res.created_at}')
    
    if res.result_json:
        data = res.result_json
        if isinstance(data, str):
            data = json.loads(data) if data else {}
        
        reqs = data.get('requirements', {})
        print(f'\n📍 Gönderilen Şehir: {reqs.get("city_name")} ({reqs.get("city_code")})')
        print(f'📍 Check In: {reqs.get("check_in")}')
        print(f'📍 Check Out: {reqs.get("check_out")}')
        print(f'📍 Adults: {reqs.get("adults")}')
        
        hotels = data.get('hotels', [])
        if hotels:
            print(f'\n✅ BAŞARILI! {len(hotels)} otel bulundu.')
            print(f'🏨 İlk Otel: {hotels[0].get("name")}')
            print(f'   Score: {hotels[0].get("score")}')
            print(f'   Price: {hotels[0].get("total_price")} {hotels[0].get("currency")}')
        else:
            error = data.get('error')
            if error:
                print(f'\n❌ HATA: {error}')
            else:
                print('\n⚠️ Otel bulunamadı (Ama hata yok).')
    else:
        print('\n⏳ İşlem devam ediyor veya result_json boş...')
finally:
    db.close()


#!/usr/bin/env python3
"""Check Hotel Match result ID 220."""
import sys
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()
try:
    res = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 220).first()
    
    if not res:
        print("❌ ID 220 bulunamadı!")
        exit(1)
    
    print(f'\n{"="*60}')
    print(f'🏨 HOTEL MATCH SONUCU (ID: 220)')
    print(f'{"="*60}')
    print(f'Status: {res.status}')
    print(f'Created: {res.created_at}')
    
    if res.result_json:
        data = res.result_json
        if isinstance(data, str):
            data = json.loads(data) if data else {}
        
        reqs = data.get('requirements', {})
        print(f'\n📍 Requirements:')
        print(f'   City: {reqs.get("city_name")} ({reqs.get("city_code")})')
        print(f'   Check In: {reqs.get("check_in")}')
        print(f'   Check Out: {reqs.get("check_out")}')
        print(f'   Adults: {reqs.get("adults")}')
        
        hotels = data.get('hotels', [])
        if hotels:
            print(f'\n✅ BAŞARILI! {len(hotels)} otel bulundu.')
            for i, hotel in enumerate(hotels[:5], 1):
                print(f'   {i}. {hotel.get("name")}')
                print(f'      Score: {hotel.get("score")}, Price: {hotel.get("total_price")} {hotel.get("currency")}')
        else:
            error = data.get('error')
            if error:
                print(f'\n❌ HATA: {error}')
            else:
                print('\n⚠️ Otel bulunamadı (işlem devam ediyor olabilir).')
    else:
        print('\n⏳ İşlem devam ediyor...')
    print(f'{"="*60}\n')
finally:
    db.close()


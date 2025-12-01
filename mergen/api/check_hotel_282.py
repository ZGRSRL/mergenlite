#!/usr/bin/env python3
"""Check Hotel Match 282."""
from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 282).first()

if result:
    print(f"Status: {result.status}")
    
    if result.status == 'completed':
        data = result.result_json if isinstance(result.result_json, dict) else json.loads(result.result_json) if result.result_json else {}
        hotels = data.get('hotels', [])
        reqs = data.get('requirements', {})
        
        print(f"\n✅ Hotel Match Tamamlandı!")
        print(f"   City: {reqs.get('city_name', 'N/A')} ({reqs.get('city_code', 'N/A')})")
        print(f"   Hotels: {len(hotels)}")
        if data.get('fallback_used'):
            print(f"   ⚠️ Fallback mekanizması kullanıldı")
        
        if hotels:
            print(f"\n   İlk 3 Otel:")
            for idx, h in enumerate(hotels[:3], 1):
                print(f"      {idx}. {h.get('name', 'N/A')} - Score: {h.get('score', 'N/A')}")
    else:
        print(f"   ⏳ Hala çalışıyor...")

db.close()


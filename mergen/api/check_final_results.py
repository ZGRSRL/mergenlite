#!/usr/bin/env python3
"""Check final results - Hotel Match 284 and Email."""
from app.db import SessionLocal
from app.models import AIAnalysisResult, AnalysisLog
import json

db = SessionLocal()

# Check Hotel Match 284
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 284).first()

print("=" * 70)
print("📊 FINAL TEST SONUÇLARI")
print("=" * 70)
print()

if result:
    print(f"🏨 Hotel Match #284:")
    print(f"   Status: {result.status}")
    
    if result.status == 'completed':
        data = result.result_json if isinstance(result.result_json, dict) else json.loads(result.result_json) if result.result_json else {}
        hotels = data.get('hotels', [])
        reqs = data.get('requirements', {})
        
        print(f"   ✅ Tamamlandı!")
        print(f"   City: {reqs.get('city_name', 'N/A')} ({reqs.get('city_code', 'N/A')})")
        print(f"   Check-In: {reqs.get('check_in', 'N/A')}")
        print(f"   Check-Out: {reqs.get('check_out', 'N/A')}")
        print(f"   Adults: {reqs.get('adults', 'N/A')}")
        print(f"   Hotels: {len(hotels)}")
        
        if data.get('fallback_used'):
            print(f"   ⚠️ Fallback mekanizması kullanıldı")
        
        if hotels:
            print(f"\n   İlk 3 Otel:")
            for idx, h in enumerate(hotels[:3], 1):
                name = h.get('name', 'Unknown Hotel')
                score = h.get('score', 'N/A')
                price = h.get('price_per_night', 'N/A')
                print(f"      {idx}. {name}")
                print(f"         Score: {score}, Price: ${price}")

# Check Email
print(f"\n📧 Email Logları:")
email_logs = db.query(AnalysisLog).filter(
    AnalysisLog.analysis_result_id == 284
).filter(
    AnalysisLog.message.ilike('%email%')
).order_by(AnalysisLog.id.desc()).limit(5).all()

if email_logs:
    print(f"   ✅ {len(email_logs)} email log bulundu:")
    for log in email_logs:
        print(f"      - {log.message[:200]}")
else:
    print(f"   ❌ Email log bulunamadı")

print()
print("=" * 70)

db.close()


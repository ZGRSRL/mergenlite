#!/usr/bin/env python3
"""Test LLM logging with new analysis."""
import requests
import time
import sys
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models import LLMCall

API_BASE = "http://localhost:8000"
OPP_ID = 6  # Houston opportunity

print("=" * 70)
print("🧪 LLM LOGGING TEST - YENİ ANALİZ")
print("=" * 70)
print()

# Get initial LLM call count
db = SessionLocal()
initial_count = db.query(LLMCall).count()
db.close()

print(f"📊 Başlangıç LLM Çağrı Sayısı: {initial_count}")
print()

# Start new SOW analysis
print("📄 Yeni SOW Analysis başlatılıyor...")
sow_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={"opportunity_id": OPP_ID, "analysis_type": "sow_draft"}
)
if sow_resp.status_code == 200:
    sow_result = sow_resp.json()
    sow_analysis_id = sow_result.get("analysis_result_id")
    print(f"   ✅ SOW Analysis ID: {sow_analysis_id}")
    
    # Wait for completion
    print(f"\n⏳ SOW Analysis tamamlanması bekleniyor...")
    for i in range(20):  # Max 10 minutes
        time.sleep(30)
        status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status')
            print(f"   Status: {status} ({i*30}s)")
            
            if status == 'completed':
                print(f"   ✅ SOW Analysis tamamlandı!")
                
                # Check LLM calls
                db = SessionLocal()
                final_count = db.query(LLMCall).count()
                new_calls = db.query(LLMCall).order_by(LLMCall.created_at.desc()).limit(5).all()
                db.close()
                
                print(f"\n📊 LLM Çağrı Kontrolü:")
                print(f"   Yeni LLM Çağrı Sayısı: {final_count - initial_count}")
                print(f"\n   Son 5 LLM Çağrısı:")
                for call in new_calls:
                    print(f"      ID: {call.id}")
                    print(f"      Provider: {call.provider}")
                    print(f"      Model: {call.model}")
                    print(f"      Agent: {call.agent_name}")
                    print(f"      Prompt: {'✅' if call.prompt else '❌'} ({len(call.prompt) if call.prompt else 0} chars)")
                    print(f"      Response: {'✅' if call.response else '❌'} ({len(call.response) if call.response else 0} chars)")
                    print(f"      Tokens: {call.prompt_tokens}/{call.completion_tokens}/{call.total_tokens}")
                    print(f"      Latency: {call.latency_ms}ms")
                    print()
                
                if final_count > initial_count:
                    print("   ✅ LLM çağrıları başarıyla kaydedildi!")
                else:
                    print("   ⚠️ Yeni LLM çağrısı kaydedilmedi")
                
                break
            elif status == 'failed':
                print(f"   ❌ SOW Analysis başarısız!")
                break
else:
    print(f"   ❌ SOW Analysis başlatılamadı: {sow_resp.status_code}")

print()
print("=" * 70)


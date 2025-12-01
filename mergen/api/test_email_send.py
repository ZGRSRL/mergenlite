#!/usr/bin/env python3
"""Test email sending for completed analysis."""
import requests
import time

API_BASE = "http://localhost:8000"
OPP_ID = 6  # Houston opportunity

print("=" * 70)
print("📧 EMAIL GÖNDERİM TESTİ")
print("=" * 70)
print()

# Start a new SOW analysis
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
    print(f"\n⏳ SOW Analysis tamamlanması bekleniyor (mail gönderilecek)...")
    for i in range(20):  # Max 10 minutes
        time.sleep(30)
        status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status')
            print(f"   Status: {status} ({i*30}s)")
            
            if status == 'completed':
                print(f"   ✅ SOW Analysis tamamlandı!")
                
                # Check email logs
                print(f"\n📧 Email logları kontrol ediliyor...")
                logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}/logs?limit=100")
                if logs_resp.status_code == 200:
                    logs = logs_resp.json()
                    email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or log.get('step') == 'email']
                    if email_logs:
                        print(f"   Email logları bulundu:")
                        for log in email_logs:
                            level = log.get('level', 'INFO')
                            message = log.get('message', '')
                            print(f"      [{level}] {message[:200]}")
                    else:
                        print(f"      (Email logları bulunamadı)")
                
                break
            elif status == 'failed':
                print(f"   ❌ SOW Analysis başarısız!")
                break
else:
    print(f"   ❌ SOW Analysis başlatılamadı: {sow_resp.status_code}")

print()
print("=" * 70)


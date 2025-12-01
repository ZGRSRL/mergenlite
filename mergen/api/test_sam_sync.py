#!/usr/bin/env python3
"""Test SAM.gov sync endpoint."""
import requests
import time
import json

API_BASE = "http://localhost:8000"

print("=" * 70)
print("🔄 SAM.GOV SYNC TEST")
print("=" * 70)
print()

# Test sync endpoint
print("📥 Sync başlatılıyor...")
print("   Parameters: NAICS=721110, days_back=7, limit=10")
resp = requests.post(
    f"{API_BASE}/api/opportunities/sync",
    params={
        "naics": "721110",
        "days_back": 7,
        "limit": 10
    }
)

if resp.status_code == 200:
    result = resp.json()
    print(f"   ✅ Sync başlatıldı!")
    print(f"   Job ID: {result.get('job_id')}")
    print()
    
    job_id = result.get('job_id')
    
    # Wait for completion
    print("⏳ Sync tamamlanması bekleniyor...")
    max_wait = 120  # 2 minutes
    for i in range(max_wait // 5):  # Check every 5 seconds
        time.sleep(5)
        status_resp = requests.get(f"{API_BASE}/api/sync-jobs/{job_id}")
        if status_resp.status_code == 200:
            status_data = status_resp.json()
            status = status_data.get('status')
            
            print(f"   Status: {status} ({i*5}s)")
            
            if status in ['completed', 'failed']:
                print(f"\n✅ Sync {status}!")
                print(f"   New: {status_data.get('count_new', 0)}")
                print(f"   Updated: {status_data.get('count_updated', 0)}")
                print(f"   Total: {status_data.get('total_processed', 0)}")
                print(f"   Attachments: {status_data.get('count_attachments', 0)}")
                break
else:
    print(f"   ❌ Sync başlatılamadı: {resp.status_code}")
    print(f"   Error: {resp.text}")

print()
print("=" * 70)


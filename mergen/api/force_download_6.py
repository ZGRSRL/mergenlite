#!/usr/bin/env python3
"""Force download attachments for opportunity 6."""
import requests
import time

API_BASE = "http://localhost:8000"
OPP_ID = 6

print("=" * 70)
print("📥 ZORLA DOKÜMAN İNDİRME - OPPORTUNITY 6")
print("=" * 70)
print()

# Reset attachments first
print("🔄 Attachments reset ediliyor...")
resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}/attachments")
if resp.status_code == 200:
    attachments = resp.json()
    print(f"   Found {len(attachments)} attachments")
    for att in attachments:
        print(f"   - {att.get('name')}: downloaded={att.get('downloaded')}, path={att.get('local_path')}")

# Start download
print("\n📥 Download başlatılıyor...")
resp = requests.post(f"{API_BASE}/api/opportunities/{OPP_ID}/download-attachments")

if resp.status_code == 200:
    job = resp.json()
    job_id = job.get('job_id')
    print(f"✅ Download job: {job_id}")
    print()
    
    # Wait and check status
    print("⏳ İndirme durumu kontrol ediliyor...")
    for i in range(120):  # 4 minutes
        time.sleep(2)
        resp = requests.get(f"{API_BASE}/api/jobs/{job_id}")
        if resp.status_code == 200:
            job_status = resp.json()
            status = job_status.get('status')
            progress = job_status.get('progress', {})
            message = progress.get('message', '')
            
            if i % 5 == 0 or status in ['completed', 'failed']:
                print(f"   [{i*2}s] Status: {status}")
                if message:
                    print(f"      Message: {message}")
            
            if status in ['completed', 'failed']:
                print(f"\n✅ Download {status}!")
                
                # Check final attachments
                resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}/attachments")
                if resp.status_code == 200:
                    attachments = resp.json()
                    downloaded = [a for a in attachments if a.get('downloaded')]
                    print(f"\n📋 Final Status:")
                    print(f"   Total: {len(attachments)}")
                    print(f"   Downloaded: {len(downloaded)}")
                    for att in downloaded:
                        print(f"   ✅ {att.get('name')}: {att.get('local_path')}")
                
                break
else:
    print(f"❌ Hata: {resp.status_code}")
    print(resp.text)


#!/usr/bin/env python3
"""Test pipeline ve email gönderimi."""
import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8000"

def get_opportunities():
    """Mevcut opportunity'leri listele."""
    resp = requests.get(f"{API_BASE}/api/opportunities/")
    if resp.status_code == 200:
        return resp.json()
    return []

def start_pipeline(opportunity_id: int, analysis_type: str = "sow_draft"):
    """Pipeline başlat."""
    payload = {
        "opportunity_id": opportunity_id,
        "analysis_type": analysis_type,
        "pipeline_version": "v1",
        "options": {}
    }
    resp = requests.post(f"{API_BASE}/api/pipeline/run", json=payload)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"Error: {resp.status_code} - {resp.text}")
        return None

def check_status(analysis_result_id: int):
    """Pipeline durumunu kontrol et."""
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_result_id}")
    if resp.status_code == 200:
        return resp.json()
    return None

def main():
    print("=== Pipeline ve Email Test ===\n")
    
    # 1. Opportunity'leri listele
    print("1. Opportunity'leri listeliyorum...")
    opps = get_opportunities()
    if not opps:
        print("❌ Hiç opportunity bulunamadı!")
        return
    
    # İlk opportunity'yi seç
    opp = opps[0] if isinstance(opps, list) else opps.get('items', [])[0] if isinstance(opps, dict) else None
    if not opp:
        print("❌ Opportunity bulunamadı!")
        return
    
    opp_id = opp.get('id') or opp.get('opportunity_id')
    opp_title = opp.get('title', 'N/A')
    print(f"✓ Opportunity seçildi: ID={opp_id}, Title={opp_title[:50]}\n")
    
    # 2. SOW Analysis başlat
    print("2. SOW Analysis pipeline'ını başlatıyorum...")
    sow_result = start_pipeline(opp_id, "sow_draft")
    if not sow_result:
        print("❌ SOW pipeline başlatılamadı!")
        return
    
    sow_analysis_id = sow_result.get('analysis_result_id')
    print(f"✓ SOW Analysis başlatıldı: ID={sow_analysis_id}")
    print(f"  Status: {sow_result.get('status')}\n")
    
    # 3. Pipeline'ın tamamlanmasını bekle
    print("3. SOW Analysis'in tamamlanmasını bekliyorum...")
    max_wait = 300  # 5 dakika
    wait_time = 0
    while wait_time < max_wait:
        status = check_status(sow_analysis_id)
        if status:
            current_status = status.get('status')
            print(f"  Status: {current_status} (bekleniyor... {wait_time}s)")
            
            if current_status == "completed":
                print(f"✓ SOW Analysis tamamlandı!\n")
                break
            elif current_status == "failed":
                print(f"❌ SOW Analysis başarısız oldu!")
                return
        
        time.sleep(5)
        wait_time += 5
    
    if wait_time >= max_wait:
        print("⚠️ Timeout: SOW Analysis tamamlanmadı, devam ediyorum...\n")
    
    # 4. Hotel Match başlat
    print("4. Hotel Match pipeline'ını başlatıyorum...")
    hotel_result = start_pipeline(opp_id, "hotel_match")
    if not hotel_result:
        print("❌ Hotel Match pipeline başlatılamadı!")
        return
    
    hotel_analysis_id = hotel_result.get('analysis_result_id')
    print(f"✓ Hotel Match başlatıldı: ID={hotel_analysis_id}")
    print(f"  Status: {hotel_result.get('status')}\n")
    
    # 5. Hotel Match'in tamamlanmasını bekle
    print("5. Hotel Match'in tamamlanmasını bekliyorum...")
    wait_time = 0
    while wait_time < max_wait:
        status = check_status(hotel_analysis_id)
        if status:
            current_status = status.get('status')
            print(f"  Status: {current_status} (bekleniyor... {wait_time}s)")
            
            if current_status == "completed":
                print(f"✓ Hotel Match tamamlandı!\n")
                break
            elif current_status == "failed":
                print(f"❌ Hotel Match başarısız oldu!")
                return
        
        time.sleep(5)
        wait_time += 5
    
    if wait_time >= max_wait:
        print("⚠️ Timeout: Hotel Match tamamlanmadı\n")
    
    # 6. Email kontrolü
    print("6. Email gönderimi kontrol ediliyor...")
    print("   (Email pipeline tamamlandığında otomatik gönderilir)")
    print("   Email adresi: config.py'den kontrol edin")
    
    print("\n=== Test Tamamlandı ===")
    print(f"SOW Analysis ID: {sow_analysis_id}")
    print(f"Hotel Match ID: {hotel_analysis_id}")
    print("\nEmail'in gönderilip gönderilmediğini kontrol etmek için:")
    print("  - SMTP loglarını kontrol edin")
    print("  - Email inbox'unuzu kontrol edin")
    print("  - Pipeline loglarını kontrol edin: /api/pipeline/results/{analysis_result_id}/logs")

if __name__ == "__main__":
    main()


import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8000"

def get_opportunities():
    """Mevcut opportunity'leri listele."""
    resp = requests.get(f"{API_BASE}/api/opportunities/")
    if resp.status_code == 200:
        return resp.json()
    return []

def start_pipeline(opportunity_id: int, analysis_type: str = "sow_draft"):
    """Pipeline başlat."""
    payload = {
        "opportunity_id": opportunity_id,
        "analysis_type": analysis_type,
        "pipeline_version": "v1",
        "options": {}
    }
    resp = requests.post(f"{API_BASE}/api/pipeline/run", json=payload)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"Error: {resp.status_code} - {resp.text}")
        return None

def check_status(analysis_result_id: int):
    """Pipeline durumunu kontrol et."""
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_result_id}")
    if resp.status_code == 200:
        return resp.json()
    return None

def main():
    print("=== Pipeline ve Email Test ===\n")
    
    # 1. Opportunity'leri listele
    print("1. Opportunity'leri listeliyorum...")
    opps = get_opportunities()
    if not opps:
        print("❌ Hiç opportunity bulunamadı!")
        return
    
    # İlk opportunity'yi seç
    opp = opps[0] if isinstance(opps, list) else opps.get('items', [])[0] if isinstance(opps, dict) else None
    if not opp:
        print("❌ Opportunity bulunamadı!")
        return
    
    opp_id = opp.get('id') or opp.get('opportunity_id')
    opp_title = opp.get('title', 'N/A')
    print(f"✓ Opportunity seçildi: ID={opp_id}, Title={opp_title[:50]}\n")
    
    # 2. SOW Analysis başlat
    print("2. SOW Analysis pipeline'ını başlatıyorum...")
    sow_result = start_pipeline(opp_id, "sow_draft")
    if not sow_result:
        print("❌ SOW pipeline başlatılamadı!")
        return
    
    sow_analysis_id = sow_result.get('analysis_result_id')
    print(f"✓ SOW Analysis başlatıldı: ID={sow_analysis_id}")
    print(f"  Status: {sow_result.get('status')}\n")
    
    # 3. Pipeline'ın tamamlanmasını bekle
    print("3. SOW Analysis'in tamamlanmasını bekliyorum...")
    max_wait = 300  # 5 dakika
    wait_time = 0
    while wait_time < max_wait:
        status = check_status(sow_analysis_id)
        if status:
            current_status = status.get('status')
            print(f"  Status: {current_status} (bekleniyor... {wait_time}s)")
            
            if current_status == "completed":
                print(f"✓ SOW Analysis tamamlandı!\n")
                break
            elif current_status == "failed":
                print(f"❌ SOW Analysis başarısız oldu!")
                return
        
        time.sleep(5)
        wait_time += 5
    
    if wait_time >= max_wait:
        print("⚠️ Timeout: SOW Analysis tamamlanmadı, devam ediyorum...\n")
    
    # 4. Hotel Match başlat
    print("4. Hotel Match pipeline'ını başlatıyorum...")
    hotel_result = start_pipeline(opp_id, "hotel_match")
    if not hotel_result:
        print("❌ Hotel Match pipeline başlatılamadı!")
        return
    
    hotel_analysis_id = hotel_result.get('analysis_result_id')
    print(f"✓ Hotel Match başlatıldı: ID={hotel_analysis_id}")
    print(f"  Status: {hotel_result.get('status')}\n")
    
    # 5. Hotel Match'in tamamlanmasını bekle
    print("5. Hotel Match'in tamamlanmasını bekliyorum...")
    wait_time = 0
    while wait_time < max_wait:
        status = check_status(hotel_analysis_id)
        if status:
            current_status = status.get('status')
            print(f"  Status: {current_status} (bekleniyor... {wait_time}s)")
            
            if current_status == "completed":
                print(f"✓ Hotel Match tamamlandı!\n")
                break
            elif current_status == "failed":
                print(f"❌ Hotel Match başarısız oldu!")
                return
        
        time.sleep(5)
        wait_time += 5
    
    if wait_time >= max_wait:
        print("⚠️ Timeout: Hotel Match tamamlanmadı\n")
    
    # 6. Email kontrolü
    print("6. Email gönderimi kontrol ediliyor...")
    print("   (Email pipeline tamamlandığında otomatik gönderilir)")
    print("   Email adresi: config.py'den kontrol edin")
    
    print("\n=== Test Tamamlandı ===")
    print(f"SOW Analysis ID: {sow_analysis_id}")
    print(f"Hotel Match ID: {hotel_analysis_id}")
    print("\nEmail'in gönderilip gönderilmediğini kontrol etmek için:")
    print("  - SMTP loglarını kontrol edin")
    print("  - Email inbox'unuzu kontrol edin")
    print("  - Pipeline loglarını kontrol edin: /api/pipeline/results/{analysis_result_id}/logs")

if __name__ == "__main__":
    main()


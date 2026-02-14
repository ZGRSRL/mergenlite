#!/usr/bin/env python3
"""
Tam Analiz Pipeline: SOW Analizi → Otel Eşleştirme → Mail Gönderimi
Tasarlandığı gibi sıralı çalışır.
"""
import sys
import requests
import time
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

mergen_api = project_root / "mergen" / "api"
sys.path.insert(0, str(mergen_api))

API_BASE = "http://localhost:8000"

print("=" * 70)
print("TAM ANALIZ PIPELINE - SOW -> HOTEL MATCH -> MAIL")
print("=" * 70)
print()

# Opportunity bilgilerini al
if len(sys.argv) > 1:
    # Notice ID veya Opportunity ID ile arama
    search_id = sys.argv[1]
    print(f"Step 0: Finding opportunity with ID: {search_id}")
    
    # Önce notice_id ile dene
    resp = requests.get(f"{API_BASE}/api/opportunities", params={"notice_id": search_id})
    if resp.status_code == 200:
        opportunities = resp.json()
        if opportunities and len(opportunities) > 0:
            opp = opportunities[0]
            opp_db_id = opp.get('id')
            opp_title = opp.get('title', 'N/A')
            print(f"   [OK] Opportunity found:")
            print(f"      Database ID: {opp_db_id}")
            print(f"      Title: {opp_title}")
            print()
        else:
            # Fallback: Try searching by opportunity_id
             resp_opp = requests.get(f"{API_BASE}/api/opportunities", params={"opportunity_id": search_id})
             if resp_opp.status_code == 200:
                 opportunities = resp_opp.json()
                 if opportunities and len(opportunities) > 0:
                     opp = opportunities[0]
                     opp_db_id = opp.get('id')
                     opp_title = opp.get('title', 'N/A')
                     print(f"   [OK] Opportunity found (via opportunity_id):")
                     print(f"      Database ID: {opp_db_id}")
                     print(f"      Title: {opp_title}")
                     print()
                 else:
                     print(f"   [ERROR] Opportunity not found with ID: {search_id}")
                     sys.exit(1)
             else:
                 print(f"   [ERROR] Opportunity not found with notice_id: {search_id}")
                 sys.exit(1)
    else:
        print(f"   [ERROR] API request failed: {resp.status_code}")
        sys.exit(1)
else:
    # Default: FIFA World Cup opportunity
    opp_db_id = 38
    print(f"Using default opportunity ID: {opp_db_id}")
    print()

# Step 1: SOW Analysis
print("=" * 70)
print("STEP 1: SOW ANALİZİ (Detaylı)")
print("=" * 70)
print()

print("Starting SOW analysis...")
sow_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": opp_db_id,
        "analysis_type": "sow_draft",
        "pipeline_version": "v1",
        "options": {
            "max_text_length": 120000  # Ensure full document analysis
        }
    }
)

if sow_resp.status_code != 200:
    print(f"   [ERROR] SOW Analysis başlatılamadı: {sow_resp.status_code}")
    print(f"      Response: {sow_resp.text}")
    sys.exit(1)

sow_result = sow_resp.json()
sow_analysis_id = sow_result.get("analysis_result_id")
print(f"   [OK] SOW Analysis başlatıldı!")
print(f"      Analysis ID: {sow_analysis_id}")
print()

# Wait for SOW completion
print("Waiting for SOW analysis to complete...")
print("   (This may take 3-5 minutes)")
print()

max_wait_sow = 300  # 5 minutes
sow_completed = False
for i in range(max_wait_sow):
    time.sleep(2)
    status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{sow_analysis_id}")
    if status_resp.status_code == 200:
        status_data = status_resp.json()
        status = status_data.get('status')
        
        # Show progress every 10 seconds
        if i % 5 == 0:
            print(f"   Status: {status} ({i*2}s)", end='\r')
        
        if status == 'completed':
            print(f"\n   [OK] SOW Analysis tamamlandı!")
            
            # Check SOW results
            result_json = status_data.get('result_json', {})
            if isinstance(result_json, str):
                result_json = json.loads(result_json) if result_json else {}
            
            doc_analysis = result_json.get('document_analysis', {})
            sow_analysis = result_json.get('sow_analysis', {})
            
            print(f"\n   Results:")
            print(f"      Documents analyzed: {doc_analysis.get('documents_analyzed', 0)}")
            print(f"      Total text length: {doc_analysis.get('total_text_length', 0)}")
            
            if sow_analysis and isinstance(sow_analysis, dict) and 'error' not in sow_analysis:
                print(f"      SOW analysis: OK")
                sow_keys = list(sow_analysis.keys())[:5]
                print(f"      SOW keys: {sow_keys}")
            else:
                print(f"      [WARNING] SOW analysis boş veya hatalı!")
                if sow_analysis and isinstance(sow_analysis, dict) and 'error' in sow_analysis:
                    print(f"      Error: {sow_analysis.get('error')}")
            
            # Check PDF
            pdf_path = status_data.get('pdf_path')
            if pdf_path:
                pdf_file = Path(pdf_path)
                if pdf_file.exists():
                    size = pdf_file.stat().st_size
                    print(f"      PDF Size: {size:,} bytes")
                    if size < 5000:
                        print(f"      [WARNING] PDF çok küçük!")
                else:
                    print(f"      [WARNING] PDF dosyası bulunamadı!")
            
            sow_completed = True
            break
        elif status == 'failed':
            print(f"\n   [FAILED] SOW Analysis başarısız!")
            error_msg = status_data.get('error_message', 'Unknown error')
            print(f"      Error: {error_msg}")
            sys.exit(1)
else:
    print(f"\n   [TIMEOUT] SOW Analysis {max_wait_sow*2} saniye içinde tamamlanamadı")
    sys.exit(1)

if not sow_completed:
    print("\n   [ERROR] SOW Analysis tamamlanamadı")
    sys.exit(1)

print()
print("=" * 70)
print("STEP 2: OTEL EŞLEŞTİRME (Hotel Match)")
print("=" * 70)
print()

# Step 2: Hotel Match (SOW analizine bağlı)
print("Starting Hotel Match analysis...")
print("   (SOW analizi sonuçlarına göre otel araması yapılacak)")
print()

hotel_resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={
        "opportunity_id": opp_db_id,
        "analysis_type": "hotel_match",
        "pipeline_version": "v1",
        "options": {
            "max_text_length": 120000
        }
    }
)

if hotel_resp.status_code != 200:
    print(f"   [ERROR] Hotel Match başlatılamadı: {hotel_resp.status_code}")
    print(f"      Response: {hotel_resp.text}")
    sys.exit(1)

hotel_result = hotel_resp.json()
hotel_analysis_id = hotel_result.get("analysis_result_id")
print(f"   [OK] Hotel Match başlatıldı!")
print(f"      Analysis ID: {hotel_analysis_id}")
print()

# Wait for Hotel Match completion
print("Waiting for Hotel Match to complete...")
print("   (This may take 2-5 minutes)")
print()

max_wait_hotel = 300  # 5 minutes
hotel_completed = False
for i in range(max_wait_hotel):
    time.sleep(2)
    hotel_status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}")
    if hotel_status_resp.status_code == 200:
        hotel_status_data = hotel_status_resp.json()
        hotel_status = hotel_status_data.get('status')
        
        # Show progress every 10 seconds
        if i % 5 == 0:
            print(f"   Status: {hotel_status} ({i*2}s)", end='\r')
        
        if hotel_status == 'completed':
            print(f"\n   [OK] Hotel Match tamamlandı!")
            
            # Check hotels
            hotel_result_json = hotel_status_data.get('result_json', {})
            if isinstance(hotel_result_json, str):
                hotel_result_json = json.loads(hotel_result_json) if hotel_result_json else {}
            
            hotels = hotel_result_json.get('hotels', [])
            print(f"\n   Results:")
            print(f"      Hotels found: {len(hotels)}")
            if hotels:
                for idx, hotel in enumerate(hotels[:5], 1):
                    name = hotel.get('name', 'N/A')
                    score = hotel.get('score', 'N/A')
                    price = hotel.get('total_price', hotel.get('price_per_night', 'N/A'))
                    print(f"      {idx}. {name}")
                    print(f"         Score: {score}, Price: {price}")
            else:
                print(f"      [WARNING] Hiç otel bulunamadı!")
            
            hotel_completed = True
            break
        elif hotel_status == 'failed':
            print(f"\n   [FAILED] Hotel Match başarısız!")
            error_msg = hotel_status_data.get('error_message', 'Unknown error')
            print(f"      Error: {error_msg}")
            # Hotel match başarısız olsa bile devam et (mail gönderilebilir)
            break
else:
    print(f"\n   [TIMEOUT] Hotel Match {max_wait_hotel*2} saniye içinde tamamlanamadı")

print()
print("=" * 70)
print("STEP 3: MAIL GÖNDERİMİ")
print("=" * 70)
print()

# Step 3: Email (hotel_match analizi otomatik olarak mail gönderir)
print("Checking email status...")
print("   (Hotel Match analizi tamamlandığında otomatik mail gönderilir)")
print()

# Check if email was sent by checking logs
logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/{hotel_analysis_id}/logs")
if logs_resp.status_code == 200:
    logs = logs_resp.json()
    email_logs = [log for log in logs if 'email' in log.get('message', '').lower() or 'mail' in log.get('message', '').lower()]
    
    if email_logs:
        print(f"   [OK] Email logları bulundu:")
        for log in email_logs[-3:]:
            level = log.get('level', 'INFO')
            message = log.get('message', '')[:150]
            print(f"      [{level}] {message}")
    else:
        print(f"   [INFO] Email logu bulunamadı (email arka planda gönderilmiş olabilir)")
        print(f"   [INFO] SMTP ayarlarını kontrol edin ve mail servis loglarını inceleyin")

print()
print("=" * 70)
print("PIPELINE TAMAMLANDI!")
print("=" * 70)
print()
print("Ozet:")
print(f"   [OK] SOW Analysis ID: {sow_analysis_id}")
print(f"   {'[OK]' if hotel_completed else '[WARN]'} Hotel Match ID: {hotel_analysis_id}")
print(f"   [MAIL] Email: Otomatik gonderildi (kontrol edin)")
print()
print("Frontend'de sonuçları görebilirsiniz:")
print(f"   http://localhost:8080/results")
print()


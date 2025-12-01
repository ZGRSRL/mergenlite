#!/usr/bin/env python3
"""Yeni analiz testi - detaylı SOW ve hotel match."""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def get_opportunities():
    resp = requests.get(f"{API_BASE}/api/opportunities/")
    if resp.status_code == 200:
        return resp.json()
    return []

def start_pipeline(opportunity_id: int, analysis_type: str = "sow_draft"):
    payload = {
        "opportunity_id": opportunity_id,
        "analysis_type": analysis_type,
        "pipeline_version": "v1",
        "options": {
            "max_text_length": 120000  # Full document analysis
        }
    }
    resp = requests.post(f"{API_BASE}/api/pipeline/run", json=payload)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"Error: {resp.status_code} - {resp.text}")
        return None

def check_status(analysis_result_id: int):
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_result_id}")
    if resp.status_code == 200:
        return resp.json()
    return None

def check_sow_content(analysis_result_id: int):
    """SOW analiz içeriğini kontrol et."""
    result = check_status(analysis_result_id)
    if not result:
        return None
    
    sow_data = result.get('result_json', {})
    if isinstance(sow_data, str):
        sow_data = json.loads(sow_data)
    
    sow_analysis = sow_data.get('sow_analysis', {})
    
    print("\n=== SOW Analysis Content Check ===")
    print(f"EventDetails keys: {list(sow_analysis.get('EventDetails', {}).keys())}")
    print(f"LodgingRequirements keys: {list(sow_analysis.get('LodgingRequirements', {}).keys())}")
    print(f"Locations count: {len(sow_analysis.get('Locations', []))}")
    print(f"TransportationRequirements: {bool(sow_analysis.get('TransportationRequirements'))}")
    print(f"Deliverables count: {len(sow_analysis.get('Deliverables', []))}")
    
    # Sample data
    event_details = sow_analysis.get('EventDetails', {})
    if event_details:
        print(f"\nEvent Name: {event_details.get('event_name')}")
        print(f"Start Date: {event_details.get('start_date')}")
        print(f"End Date: {event_details.get('end_date')}")
    
    lodging = sow_analysis.get('LodgingRequirements', {})
    if lodging:
        print(f"\nRooms Min: {lodging.get('rooms_per_city_min')}")
        print(f"Rooms Max: {lodging.get('rooms_per_city_max')}")
        print(f"Max Stay Days: {lodging.get('max_stay_days_per_city')}")
    
    return sow_analysis

def main():
    print("=== Yeni Detaylı Analiz Testi ===\n")
    
    # Get opportunity
    opps = get_opportunities()
    if not opps:
        print("❌ Hiç opportunity bulunamadı!")
        return
    
    opp = opps[0] if isinstance(opps, list) else opps.get('items', [])[0] if isinstance(opps, dict) else None
    if not opp:
        print("❌ Opportunity bulunamadı!")
        return
    
    opp_id = opp.get('id') or opp.get('opportunity_id')
    print(f"✓ Opportunity: ID={opp_id}\n")
    
    # Start SOW Analysis
    print("1. SOW Analysis başlatılıyor (120k karakter limiti ile)...")
    sow_result = start_pipeline(opp_id, "sow_draft")
    if not sow_result:
        print("❌ SOW pipeline başlatılamadı!")
        return
    
    sow_id = sow_result.get('analysis_result_id')
    print(f"✓ SOW Analysis ID: {sow_id}\n")
    
    # Wait for completion
    print("2. SOW Analysis tamamlanmasını bekliyorum...")
    max_wait = 300
    wait_time = 0
    while wait_time < max_wait:
        status = check_status(sow_id)
        if status:
            current_status = status.get('status')
            if wait_time % 15 == 0:  # Her 15 saniyede bir yazdır
                print(f"  Status: {current_status} ({wait_time}s)")
            
            if current_status == "completed":
                print(f"✓ SOW Analysis tamamlandı!\n")
                break
            elif current_status == "failed":
                print(f"❌ SOW Analysis başarısız!")
                return
        
        time.sleep(5)
        wait_time += 5
    
    # Check SOW content
    sow_content = check_sow_content(sow_id)
    
    # Start Hotel Match
    print("\n3. Hotel Match başlatılıyor (SOW analizini kullanarak)...")
    hotel_result = start_pipeline(opp_id, "hotel_match")
    if not hotel_result:
        print("❌ Hotel Match başlatılamadı!")
        return
    
    hotel_id = hotel_result.get('analysis_result_id')
    print(f"✓ Hotel Match ID: {hotel_id}\n")
    
    # Wait for hotel match
    print("4. Hotel Match tamamlanmasını bekliyorum...")
    wait_time = 0
    while wait_time < max_wait:
        status = check_status(hotel_id)
        if status:
            current_status = status.get('status')
            if wait_time % 15 == 0:
                print(f"  Status: {current_status} ({wait_time}s)")
            
            if current_status == "completed":
                print(f"✓ Hotel Match tamamlandı!\n")
                break
            elif current_status == "failed":
                print(f"❌ Hotel Match başarısız!")
                error = status.get('result_json', {}).get('error', 'Unknown error')
                print(f"  Error: {error}")
                return
        
        time.sleep(5)
        wait_time += 5
    
    print("\n=== Test Tamamlandı ===")
    print(f"SOW Analysis ID: {sow_id}")
    print(f"Hotel Match ID: {hotel_id}")
    print("\nEmail otomatik gönderilecek!")

if __name__ == "__main__":
    main()


"""Yeni analiz testi - detaylı SOW ve hotel match."""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def get_opportunities():
    resp = requests.get(f"{API_BASE}/api/opportunities/")
    if resp.status_code == 200:
        return resp.json()
    return []

def start_pipeline(opportunity_id: int, analysis_type: str = "sow_draft"):
    payload = {
        "opportunity_id": opportunity_id,
        "analysis_type": analysis_type,
        "pipeline_version": "v1",
        "options": {
            "max_text_length": 120000  # Full document analysis
        }
    }
    resp = requests.post(f"{API_BASE}/api/pipeline/run", json=payload)
    if resp.status_code == 200:
        return resp.json()
    else:
        print(f"Error: {resp.status_code} - {resp.text}")
        return None

def check_status(analysis_result_id: int):
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_result_id}")
    if resp.status_code == 200:
        return resp.json()
    return None

def check_sow_content(analysis_result_id: int):
    """SOW analiz içeriğini kontrol et."""
    result = check_status(analysis_result_id)
    if not result:
        return None
    
    sow_data = result.get('result_json', {})
    if isinstance(sow_data, str):
        sow_data = json.loads(sow_data)
    
    sow_analysis = sow_data.get('sow_analysis', {})
    
    print("\n=== SOW Analysis Content Check ===")
    print(f"EventDetails keys: {list(sow_analysis.get('EventDetails', {}).keys())}")
    print(f"LodgingRequirements keys: {list(sow_analysis.get('LodgingRequirements', {}).keys())}")
    print(f"Locations count: {len(sow_analysis.get('Locations', []))}")
    print(f"TransportationRequirements: {bool(sow_analysis.get('TransportationRequirements'))}")
    print(f"Deliverables count: {len(sow_analysis.get('Deliverables', []))}")
    
    # Sample data
    event_details = sow_analysis.get('EventDetails', {})
    if event_details:
        print(f"\nEvent Name: {event_details.get('event_name')}")
        print(f"Start Date: {event_details.get('start_date')}")
        print(f"End Date: {event_details.get('end_date')}")
    
    lodging = sow_analysis.get('LodgingRequirements', {})
    if lodging:
        print(f"\nRooms Min: {lodging.get('rooms_per_city_min')}")
        print(f"Rooms Max: {lodging.get('rooms_per_city_max')}")
        print(f"Max Stay Days: {lodging.get('max_stay_days_per_city')}")
    
    return sow_analysis

def main():
    print("=== Yeni Detaylı Analiz Testi ===\n")
    
    # Get opportunity
    opps = get_opportunities()
    if not opps:
        print("❌ Hiç opportunity bulunamadı!")
        return
    
    opp = opps[0] if isinstance(opps, list) else opps.get('items', [])[0] if isinstance(opps, dict) else None
    if not opp:
        print("❌ Opportunity bulunamadı!")
        return
    
    opp_id = opp.get('id') or opp.get('opportunity_id')
    print(f"✓ Opportunity: ID={opp_id}\n")
    
    # Start SOW Analysis
    print("1. SOW Analysis başlatılıyor (120k karakter limiti ile)...")
    sow_result = start_pipeline(opp_id, "sow_draft")
    if not sow_result:
        print("❌ SOW pipeline başlatılamadı!")
        return
    
    sow_id = sow_result.get('analysis_result_id')
    print(f"✓ SOW Analysis ID: {sow_id}\n")
    
    # Wait for completion
    print("2. SOW Analysis tamamlanmasını bekliyorum...")
    max_wait = 300
    wait_time = 0
    while wait_time < max_wait:
        status = check_status(sow_id)
        if status:
            current_status = status.get('status')
            if wait_time % 15 == 0:  # Her 15 saniyede bir yazdır
                print(f"  Status: {current_status} ({wait_time}s)")
            
            if current_status == "completed":
                print(f"✓ SOW Analysis tamamlandı!\n")
                break
            elif current_status == "failed":
                print(f"❌ SOW Analysis başarısız!")
                return
        
        time.sleep(5)
        wait_time += 5
    
    # Check SOW content
    sow_content = check_sow_content(sow_id)
    
    # Start Hotel Match
    print("\n3. Hotel Match başlatılıyor (SOW analizini kullanarak)...")
    hotel_result = start_pipeline(opp_id, "hotel_match")
    if not hotel_result:
        print("❌ Hotel Match başlatılamadı!")
        return
    
    hotel_id = hotel_result.get('analysis_result_id')
    print(f"✓ Hotel Match ID: {hotel_id}\n")
    
    # Wait for hotel match
    print("4. Hotel Match tamamlanmasını bekliyorum...")
    wait_time = 0
    while wait_time < max_wait:
        status = check_status(hotel_id)
        if status:
            current_status = status.get('status')
            if wait_time % 15 == 0:
                print(f"  Status: {current_status} ({wait_time}s)")
            
            if current_status == "completed":
                print(f"✓ Hotel Match tamamlandı!\n")
                break
            elif current_status == "failed":
                print(f"❌ Hotel Match başarısız!")
                error = status.get('result_json', {}).get('error', 'Unknown error')
                print(f"  Error: {error}")
                return
        
        time.sleep(5)
        wait_time += 5
    
    print("\n=== Test Tamamlandı ===")
    print(f"SOW Analysis ID: {sow_id}")
    print(f"Hotel Match ID: {hotel_id}")
    print("\nEmail otomatik gönderilecek!")

if __name__ == "__main__":
    main()


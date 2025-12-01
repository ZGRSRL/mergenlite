#!/usr/bin/env python3
"""FIFA için yeni analiz testi."""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def start_pipeline(opportunity_id: int, analysis_type: str = "sow_draft", options: dict = None):
    payload = {
        "opportunity_id": opportunity_id,
        "analysis_type": analysis_type,
        "pipeline_version": "v1",
        "options": options or {}
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
    """SOW analiz içeriğini detaylı kontrol et."""
    result = check_status(analysis_result_id)
    if not result:
        return None
    
    sow_data = result.get('result_json', {})
    if isinstance(sow_data, str):
        sow_data = json.loads(sow_data)
    
    sow_analysis = sow_data.get('sow_analysis', {})
    analyzed_docs = sow_data.get('analyzed_documents', [])
    
    print("\n=== SOW Analysis Detaylı Kontrol ===")
    print(f"Toplam Doküman: {len(analyzed_docs)}")
    
    total_text = 0
    for i, doc in enumerate(analyzed_docs, 1):
        text_len = doc.get('text_length', 0)
        total_text += text_len
        print(f"  Doküman {i}: {doc.get('attachment_name', 'N/A')} - {text_len} karakter")
    
    print(f"\nToplam Metin: {total_text} karakter")
    print(f"SOW Analysis Var: {'Evet' if sow_analysis else 'Hayır'}")
    
    if sow_analysis:
        print(f"\nSOW Analysis Keys: {list(sow_analysis.keys())[:15]}")
        
        event_details = sow_analysis.get('EventDetails', {})
        if event_details:
            print(f"\nEventDetails:")
            print(f"  Event Name: {event_details.get('event_name')}")
            print(f"  Start Date: {event_details.get('start_date')}")
            print(f"  End Date: {event_details.get('end_date')}")
        else:
            print("\nEventDetails: BOŞ!")
        
        locations = sow_analysis.get('Locations', [])
        print(f"\nLocations: {len(locations)} şehir")
        if locations:
            print(f"  İlk şehir: {locations[0].get('city', 'N/A')}")
        
        lodging = sow_analysis.get('LodgingRequirements', {})
        if lodging:
            print(f"\nLodgingRequirements:")
            print(f"  Min Rooms: {lodging.get('rooms_per_city_min')}")
            print(f"  Max Rooms: {lodging.get('rooms_per_city_max')}")
        else:
            print("\nLodgingRequirements: BOŞ!")
    
    return sow_analysis

def wait_for_completion(analysis_result_id: int, name: str, max_wait: int = 300):
    print(f"\n{name} tamamlanmasını bekliyorum...")
    wait_time = 0
    while wait_time < max_wait:
        status = check_status(analysis_result_id)
        if status:
            current_status = status.get('status')
            if wait_time % 20 == 0:
                print(f"  Status: {current_status} ({wait_time}s)")
            
            if current_status == "completed":
                print(f"✓ {name} tamamlandı!")
                return True
            elif current_status == "failed":
                print(f"❌ {name} başarısız!")
                error = status.get('result_json', {})
                if isinstance(error, str):
                    try:
                        error = json.loads(error)
                    except:
                        pass
                print(f"  Error: {error.get('error', 'Unknown error')}")
                return False
        
        time.sleep(5)
        wait_time += 5
    
    print(f"⚠️ Timeout: {name} tamamlanmadı")
    return False

def main():
    print("=== FIFA Analiz Testi ===\n")
    
    # Get opportunity
    resp = requests.get(f"{API_BASE}/api/opportunities/")
    if resp.status_code != 200:
        print("❌ Opportunity'ler alınamadı!")
        return
    
    opps = resp.json()
    opp = opps[0] if isinstance(opps, list) else opps.get('items', [])[0] if isinstance(opps, dict) else None
    if not opp:
        print("❌ Opportunity bulunamadı!")
        return
    
    opp_id = opp.get('id') or opp.get('opportunity_id')
    print(f"✓ Opportunity ID: {opp_id}")
    print(f"  Title: {opp.get('title', 'N/A')[:50]}\n")
    
    # Start SOW Analysis
    print("1. SOW Analysis başlatılıyor (tüm dokümanlar birleştirilecek)...")
    sow_result = start_pipeline(opp_id, "sow_draft", {
        "max_text_length": 120000
    })
    if not sow_result:
        print("❌ SOW pipeline başlatılamadı!")
        return
    
    sow_id = sow_result.get('analysis_result_id')
    print(f"✓ SOW Analysis ID: {sow_id}")
    
    if not wait_for_completion(sow_id, "SOW Analysis"):
        return
    
    # Check SOW content
    sow_content = check_sow_content(sow_id)
    
    if not sow_content or not sow_content.get('EventDetails'):
        print("\n⚠️ SOW Analysis boş veya eksik!")
        print("Muhtemelen PDF'ler düzgün extract edilemedi.")
        return
    
    print("\n✓ SOW Analysis başarılı ve detaylı!")
    
    # Start Hotel Match
    print("\n2. Hotel Match başlatılıyor...")
    hotel_result = start_pipeline(opp_id, "hotel_match", {
        "use_sow_analysis": True,
        "use_document_analysis": True
    })
    if not hotel_result:
        print("❌ Hotel Match başlatılamadı!")
        return
    
    hotel_id = hotel_result.get('analysis_result_id')
    print(f"✓ Hotel Match ID: {hotel_id}")
    
    if not wait_for_completion(hotel_id, "Hotel Match"):
        print("⚠️ Hotel Match başarısız ama devam ediyorum...")
    
    print("\n=== Analiz Tamamlandı ===")
    print(f"SOW Analysis ID: {sow_id}")
    print(f"Hotel Match ID: {hotel_id}")
    print("\n✓ Email otomatik olarak gönderilecek!")
    print("  Alıcı: ozgursarli@hotmail.com")

if __name__ == "__main__":
    main()


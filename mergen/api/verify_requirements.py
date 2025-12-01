#!/usr/bin/env python3
"""Test build_hotel_match_requirements function directly."""
import logging
import json
import sys
from pathlib import Path

# Add project root to path (script is in /app/verify_requirements.py)
# So we need to add /app to path
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models import AIAnalysisResult, Opportunity
from app.services.opportunity_context import build_hotel_match_requirements

# Loglamayı konsola açalım
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger("app.services.opportunity_context")
logger.setLevel(logging.INFO)

def test_logic():
    print("\n" + "=" * 60)
    print("=== REQUIREMENTS LOGIC TEST ===")
    print("=" * 60)
    
    db = SessionLocal()
    
    try:
        # 1. Opportunity ve SOW Verisini Çek
        opp_id = 3
        sow_result_id = 204  # Başarılı SOW analizinin ID'si
        
        opp = db.query(Opportunity).filter(Opportunity.id == opp_id).first()
        sow_res = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == sow_result_id).first()
        
        if not opp:
            print(f"❌ Opportunity {opp_id} bulunamadı.")
            return
        
        if not sow_res:
            print(f"❌ SOW Analysis result {sow_result_id} bulunamadı.")
            return
        
        print(f"\n✅ Opportunity: {opp.title}")
        print(f"✅ SOW Result ID: {sow_res.id}, Status: {sow_res.status}")
        
        sow_data = sow_res.result_json
        if isinstance(sow_data, str):
            sow_data = json.loads(sow_data) if sow_data else {}
        
        sow_analysis = sow_data.get("sow_analysis")
        if not sow_analysis:
            print("❌ SOW Analysis verisi yok!")
            return
        
        # Locations Array Kontrolü
        locs = sow_analysis.get("Locations", [])
        print(f"\n📊 Input Data - Locations Count: {len(locs) if locs else 0}")
        if locs and len(locs) > 0:
            print(f"📊 Input Data - First Location Raw: {json.dumps(locs[0], indent=2, ensure_ascii=False)}")
            print(f"📊 Input Data - First Location Keys: {list(locs[0].keys()) if isinstance(locs[0], dict) else 'N/A'}")
        
        # 2. FONKSİYONU ÇAĞIR (Kritik Nokta)
        print("\n" + "-" * 60)
        print("--- FONKSİYON ÇAĞRILIYOR ---")
        print("-" * 60)
        
        try:
            reqs = build_hotel_match_requirements(
                opportunity=opp,
                options={},  # Manuel options yok
                sow_analysis=sow_analysis,
                document_analysis=None
            )
            
            print("\n" + "-" * 60)
            print("--- SONUÇ ---")
            print("-" * 60)
            print(f"City Name: {reqs.get('city_name')}")
            print(f"City Code: {reqs.get('city_code')}")
            print(f"Check In:  {reqs.get('check_in')}")
            print(f"Check Out: {reqs.get('check_out')}")
            print(f"Adults:    {reqs.get('adults')}")
            print(f"SOW Used:  {reqs.get('sow_analysis_used')}")
            
            if reqs.get('city_code') == 'PHL':
                print("\n✅ BAŞARILI! Philadelphia (PHL) çözümlendi.")
            elif reqs.get('city_code'):
                print(f"\n⚠️ City Code bulundu ama PHL değil: {reqs.get('city_code')}")
            else:
                print("\n❌ BAŞARISIZ! City Code hala eksik.")
                
        except Exception as e:
            print(f"\n❌ HATA OLUŞTU: {e}")
            import traceback
            traceback.print_exc()
    
    finally:
        db.close()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_logic()


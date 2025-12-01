#!/usr/bin/env python3
"""Test complex table extraction for opportunity 6 (Houston) - re-analyze with improved parser."""
import requests
import time
import json

API_BASE = "http://localhost:8000"
OPP_ID = 6  # Houston opportunity

print("=" * 70)
print("🔍 KARMAŞIK TABLO TESTİ - HOUSTON (ID 6)")
print("=" * 70)
print()

# Start new SOW analysis
print("📄 Yeni SOW Analysis başlatılıyor (karmaşık tablo desteği ile)...")
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
                
                # Check results
                result_json = status_data.get('result_json', {})
                sow_analysis = result_json.get('sow_analysis', {})
                doc_analysis = result_json.get('document_analysis', {})
                
                print(f"\n📊 İstatistikler:")
                print(f"   Words: {doc_analysis.get('total_word_count', 0):,}")
                print(f"   Tables: {doc_analysis.get('total_tables', 0)}")
                
                # Check Function Space
                function_space = sow_analysis.get('FunctionSpaceRequirements', {})
                room_types = function_space.get('room_types', [])
                setup_reqs = function_space.get('setup_requirements', [])
                capacity_reqs = function_space.get('capacity_requirements', [])
                
                print(f"\n🏢 Function Space Requirements:")
                print(f"   Room Types: {len(room_types)}")
                if room_types:
                    for rt in room_types[:5]:
                        print(f"      - {rt}")
                print(f"   Setup Requirements: {len(setup_reqs)}")
                if setup_reqs:
                    for sr in setup_reqs[:5]:
                        print(f"      - {sr}")
                print(f"   Capacity Requirements: {len(capacity_reqs)}")
                if capacity_reqs:
                    for cr in capacity_reqs[:5]:
                        print(f"      - {cr}")
                
                # Check AV Requirements
                av_reqs = sow_analysis.get('AVRequirements', {})
                room_reqs = av_reqs.get('room_requirements', [])
                special_notes = av_reqs.get('special_notes', [])
                
                print(f"\n🎤 AV Requirements:")
                print(f"   Room Requirements: {len(room_reqs)}")
                if room_reqs:
                    for rr in room_reqs[:5]:
                        if isinstance(rr, dict):
                            print(f"      - {str(rr)[:100]}")
                        else:
                            print(f"      - {str(rr)[:100]}")
                print(f"   Special Notes: {len(special_notes)}")
                if special_notes:
                    for sn in special_notes[:5]:
                        print(f"      - {str(sn)[:100]}")
                
                # Check F&B Requirements
                fb_reqs = sow_analysis.get('FoodAndBeverageRequirements', {})
                daily_breakdown = fb_reqs.get('daily_breakdown', [])
                
                print(f"\n🍽️ Food & Beverage Requirements:")
                print(f"   Daily Breakdown: {len(daily_breakdown)}")
                if daily_breakdown:
                    for db in daily_breakdown[:5]:
                        if isinstance(db, dict):
                            print(f"      - {db.get('date', 'N/A')}: {db.get('meal_type', 'N/A')} ({db.get('headcount', 'N/A')} people)")
                        else:
                            print(f"      - {str(db)[:100]}")
                
                # Check data quality issues
                data_quality = sow_analysis.get('data_quality_issues', [])
                if data_quality:
                    print(f"\n⚠️ Data Quality Issues:")
                    for issue in data_quality:
                        print(f"      - {issue}")
                
                # Summary
                print(f"\n✅ Özet:")
                has_function_space = len(room_types) > 0 or len(setup_reqs) > 0
                has_av = len(room_reqs) > 0 or len(special_notes) > 0
                has_fb = len(daily_breakdown) > 0
                
                print(f"   Function Space: {'✅' if has_function_space else '❌'}")
                print(f"   AV Requirements: {'✅' if has_av else '❌'}")
                print(f"   F&B Requirements: {'✅' if has_fb else '❌'}")
                
                if has_function_space and has_av and has_fb:
                    print(f"\n🎉 TÜM VERİLER BAŞARIYLA ÇIKARILDI!")
                elif has_function_space or has_av or has_fb:
                    print(f"\n⚠️ Bazı veriler çıkarıldı, ancak tamamı değil.")
                else:
                    print(f"\n❌ Veriler hala çıkarılamadı.")
                
                break
            elif status == 'failed':
                print(f"   ❌ SOW Analysis başarısız!")
                break
else:
    print(f"   ❌ SOW Analysis başlatılamadı: {sow_resp.status_code}")

print()
print("=" * 70)


from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Analysis 253'ü detaylı kontrol et
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 253).first()

if result:
    print("=" * 70)
    print("📊 FIFA ANALİZ 253 - DETAYLI RAPOR")
    print("=" * 70)
    print()
    
    if result.result_json:
        data = result.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        sow_analysis = data.get('sow_analysis', {})
        if sow_analysis:
            # Function Space Requirements
            func_space = sow_analysis.get('FunctionSpaceRequirements', {})
            print("📐 Function Space Requirements:")
            setup_reqs = func_space.get('setup_requirements', [])
            room_types = func_space.get('room_types', [])
            print(f"   Setup Requirements: {len(setup_reqs)}")
            for req in setup_reqs[:5]:
                print(f"      - {req}")
            print(f"   Room Types: {len(room_types)}")
            for rt in room_types[:5]:
                print(f"      - {rt}")
            
            # AV Requirements
            av_reqs = sow_analysis.get('AVRequirements', {})
            print(f"\n🎤 AV Requirements:")
            room_reqs = av_reqs.get('room_requirements', [])
            special_notes = av_reqs.get('special_notes', [])
            print(f"   Room Requirements: {len(room_reqs)}")
            for req in room_reqs[:5]:
                print(f"      - {req}")
            print(f"   Special Notes: {len(special_notes)}")
            for note in special_notes[:5]:
                print(f"      - {note}")
            
            # F&B Requirements
            fb_reqs = sow_analysis.get('FoodAndBeverageRequirements', {})
            print(f"\n🍽️ Food & Beverage Requirements:")
            daily_breakdown = fb_reqs.get('daily_breakdown', [])
            print(f"   Daily Breakdown: {len(daily_breakdown)}")
            for item in daily_breakdown[:5]:
                if isinstance(item, dict):
                    print(f"      - {item}")
                # Show key details
                    for key in ['day', 'date', 'time', 'headcount', 'menu']:
                        if key in item:
                            print(f"        {key}: {item[key]}")
                else:
                    print(f"      - {item}")
            
            # Locations
            locations = sow_analysis.get('Locations', [])
            print(f"\n🏙️ Locations: {len(locations)}")
            for i, loc in enumerate(locations[:3], 1):
                if isinstance(loc, dict):
                    print(f"   {i}. {loc.get('city', 'N/A')}")
                    print(f"      Stadium: {loc.get('stadium', 'N/A')}")
                    print(f"      Start: {loc.get('start_date', 'N/A')}")
                    print(f"      Days: {loc.get('num_days', 'N/A')}")
            
            # Data Quality Issues
            data_quality = sow_analysis.get('data_quality_issues', [])
            if data_quality:
                print(f"\n⚠️ Data Quality Issues: {len(data_quality)}")
                for issue in data_quality:
                    print(f"      - {issue}")
            else:
                print(f"\n✅ Data Quality: No issues reported")

db.close()


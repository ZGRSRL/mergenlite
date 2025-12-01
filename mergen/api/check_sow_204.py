from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Check SOW 204
sow204 = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 204).first()
if sow204:
    print(f"SOW 204: {sow204.status}")
    if sow204.result_json:
        data = sow204.result_json
        if isinstance(data, str):
            data = json.loads(data)
        sow_analysis = data.get('sow_analysis', {})
        locations = sow_analysis.get('Locations', [])
        print(f"Locations count: {len(locations)}")
        if locations:
            print(f"First city: {locations[0].get('city', 'N/A')}")
            print(f"✅ SOW 204 has locations - can use for hotel match")
        else:
            print("❌ SOW 204 has no locations")
else:
    print("SOW 204 not found")

# Find SOW with locations
sows = db.query(AIAnalysisResult).filter(
    AIAnalysisResult.opportunity_id == 3,
    AIAnalysisResult.analysis_type.in_(['sow', 'sow_draft']),
    AIAnalysisResult.status == 'completed'
).order_by(AIAnalysisResult.created_at.desc()).limit(10).all()

print("\nSearching for SOW with locations...")
for s in sows:
    if s.result_json:
        data = s.result_json
        if isinstance(data, str):
            data = json.loads(data)
        sow_analysis = data.get('sow_analysis', {})
        locations = sow_analysis.get('Locations', [])
        if locations and len(locations) > 0:
            print(f"✅ Found SOW ID {s.id} with {len(locations)} locations")
            print(f"   First city: {locations[0].get('city', 'N/A')}")
            break

db.close()


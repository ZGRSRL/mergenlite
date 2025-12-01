from app.db import SessionLocal
from app.models import Opportunity
from datetime import datetime

db = SessionLocal()

# Notice IDs from the list
notice_ids = [
    "bc3103b932314ec3b840c2e3d711e7bd",
    "c2adb79f5ce84717bd0ccc8584809ac9",  # Houston - already analyzed
    "e8ec6a214de419b8957706330d5bb27",
    "c4f1986d6b0245eba0a30b50027c6a02",
    "bf468a717513410eb93a6a4e848b573e",
    "b72302ebb958427baf9ada9aa7b62acd",
    "9c63466555c147d5acf4e13ed34e2006",
    "9499e420a9784292b39944e6335c124f",
    "58ee30c060e842779d51eec11b10fd4d",
    "538b9954bedd4ec4982f56ba9b2f1da0",
    "3cb86dc0a6804d95805ab18084763a3b",
    "37b30be76a2849ef890a76c144e780c9",
    "1cee4139272a4492a50dfde08e452edc",
    "00988be44b354a30ab4aa7b493ae5fd0",
    "fac76f84bc9a43ea9795a7fd6ccc0d26",
    "d66b7f24fcfc4add93f3cf7d4d397786",
    "ceb88dbfe4ce4c1384b10e60837bafab",
]

print("=" * 70)
print("📋 OPPORTUNITY DURUM KONTROLÜ")
print("=" * 70)
print()

found = 0
not_found = []

for notice_id in notice_ids:
    opp = db.query(Opportunity).filter(Opportunity.notice_id == notice_id).first()
    if opp:
        found += 1
        # Check if analyzed
        from app.models import AIAnalysisResult
        analysis = db.query(AIAnalysisResult).filter(
            AIAnalysisResult.opportunity_id == opp.id
        ).order_by(AIAnalysisResult.created_at.desc()).first()
        
        status = "✅"
        analysis_info = ""
        if analysis:
            analysis_info = f" (Analysis: {analysis.analysis_type}, Status: {analysis.status})"
        
        print(f"{status} {opp.title[:60]}")
        print(f"   ID: {opp.id}, Notice: {notice_id[:20]}...{analysis_info}")
    else:
        not_found.append(notice_id)

print()
print(f"📊 Özet:")
print(f"   ✅ Sistemde: {found}/{len(notice_ids)}")
print(f"   ❌ Sistemde yok: {len(not_found)}")

if not_found:
    print(f"\n⚠️ Sistemde olmayan opportunity'ler:")
    for notice_id in not_found[:5]:
        print(f"   - {notice_id}")

db.close()


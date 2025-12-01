from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# Check analysis 233
result = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 233).first()
if result:
    print(f"Analysis 233: {result.analysis_type} - {result.status}")
    if result.result_json:
        data = result.result_json
        if isinstance(data, str):
            data = json.loads(data)
        
        # Check document analysis
        doc_analysis = data.get('document_analysis', {})
        total_words = doc_analysis.get('total_word_count', 0)
        total_chars = doc_analysis.get('total_text_length', 0)
        print(f"\nDocument Analysis:")
        print(f"  Total words: {total_words}")
        print(f"  Total chars: {total_chars}")
        
        if total_words >= 18000:
            print(f"  ✅ SUCCESS! Got {total_words} words (expected ~18,000+)")
        elif total_words > 0:
            print(f"  ⚠️ WARNING: Only {total_words} words (expected ~18,000+)")
        else:
            print(f"  ❌ ERROR: No text extracted!")
        
        # Check SOW analysis
        sow = data.get('sow_analysis', {})
        if sow:
            print(f"\nSOW Analysis:")
            locations = sow.get('Locations', []) if isinstance(sow, dict) else []
            print(f"  Locations: {len(locations)}")
            if locations:
                print(f"  ✅ SUCCESS! First city: {locations[0].get('city', 'N/A')}")
            else:
                print(f"  ⚠️ No locations extracted")
        else:
            print(f"\n❌ No SOW analysis (AutoGen may not have run)")
        
        # Check analyzed documents
        analyzed_docs = data.get('analyzed_documents', [])
        print(f"\nAnalyzed Documents: {len(analyzed_docs)}")
        for i, doc in enumerate(analyzed_docs[:3], 1):
            words = doc.get('word_count', 0)
            chars = doc.get('text_length', 0)
            print(f"  Doc {i}: {words} words, {chars} chars")
    else:
        print("  ❌ No result_json")
else:
    print("Analysis 233 not found")

db.close()


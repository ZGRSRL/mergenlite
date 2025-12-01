from app.db import SessionLocal
from app.models import AIAnalysisResult
import json

db = SessionLocal()

# SOW 240'ı kontrol et
sow = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 240).first()

if sow and sow.result_json:
    data = sow.result_json
    if isinstance(data, str):
        data = json.loads(data)
    
    # Analyzed documents
    analyzed_docs = data.get('analyzed_documents', [])
    print(f"Analyzed Documents: {len(analyzed_docs)}")
    
    for i, doc in enumerate(analyzed_docs, 1):
        text = doc.get('extracted_text', '')
        tables = doc.get('tables', [])
        print(f"\nDoc {i} ({doc.get('attachment_name', 'N/A')}):")
        print(f"  Text length: {len(text)}")
        print(f"  Tables: {len(tables)}")
        
        # Tablolar metin içinde var mı?
        if '[TABLE' in text:
            print(f"  ✅ Tablolar metin içinde var!")
            # Tüm tabloları bul
            import re
            table_matches = re.findall(r'\[TABLE \d+\].*?(?=\[TABLE|\Z)', text, re.DOTALL)
            print(f"  Found {len(table_matches)} table markers in text")
            if table_matches:
                print(f"  First table preview (first 300 chars):")
                print(f"  {table_matches[0][:300]}")
        else:
            print(f"  ❌ Tablolar metin içinde yok!")
        
        # Ayrı tables array'i var mı?
        if tables:
            print(f"  ✅ Ayrı tables array var: {len(tables)} tables")
            if tables[0]:
                print(f"  First table first row: {tables[0][0] if isinstance(tables[0], list) and len(tables[0]) > 0 else 'N/A'}")

db.close()


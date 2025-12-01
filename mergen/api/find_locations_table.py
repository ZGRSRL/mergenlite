from app.db import SessionLocal
from app.models import AIAnalysisResult
import json
import re

db = SessionLocal()

# SOW 240'ı kontrol et
sow = db.query(AIAnalysisResult).filter(AIAnalysisResult.id == 240).first()

if sow and sow.result_json:
    data = sow.result_json
    if isinstance(data, str):
        data = json.loads(data)
    
    analyzed_docs = data.get('analyzed_documents', [])
    
    # Tüm metni birleştir
    all_text = ""
    for doc in analyzed_docs:
        text = doc.get('extracted_text', '')
        if text:
            all_text += f"\n\n--- {doc.get('attachment_name', 'Doc')} ---\n\n"
            all_text += text
    
    print(f"Total combined text length: {len(all_text)}")
    
    # Locations tablosunu ara
    print("\n" + "=" * 60)
    print("LOCATIONS TABLOSU ARAMA")
    print("=" * 60)
    
    # "LOCATIONS" veya "Locations" kelimesini ara
    locations_patterns = [
        r'LOCATIONS?.*?TABLE',
        r'Locations?.*?Table',
        r'Philadelphia',
        r'Atlanta',
        r'City.*?Stadium.*?ZIP',
    ]
    
    found_locations = False
    for pattern in locations_patterns:
        matches = re.finditer(pattern, all_text, re.IGNORECASE)
        for match in matches:
            start = max(0, match.start() - 100)
            end = min(len(all_text), match.end() + 500)
            print(f"\n✅ Bulundu: '{pattern}'")
            print(f"Context:")
            print(f"{all_text[start:end]}")
            found_locations = True
            break
        if found_locations:
            break
    
    if not found_locations:
        print("\n❌ Locations tablosu bulunamadı!")
        print("Tabloları kontrol ediyorum...")
        
        # Tüm tabloları listele
        table_matches = re.findall(r'\[TABLE \d+\].*?(?=\[TABLE|\Z)', all_text, re.DOTALL)
        print(f"\nToplam {len(table_matches)} tablo bulundu:")
        for i, table in enumerate(table_matches[:10], 1):
            # İlk 200 karakteri göster
            preview = table[:200].replace('\n', ' ')
            print(f"  Table {i}: {preview}...")
            
            # Philadelphia veya şehir ismi var mı?
            if 'philadelphia' in table.lower() or 'atlanta' in table.lower() or 'city' in table.lower():
                print(f"    ✅ Bu tablo şehir bilgisi içeriyor olabilir!")
                print(f"    Full table (first 1000 chars):")
                print(f"    {table[:1000]}")

db.close()


from app.db import SessionLocal
from app.models import OpportunityAttachment
from app.services.parsing.document_analyzer import analyze_document
from pathlib import Path

db = SessionLocal()

print("=" * 70)
print("📄 DOKÜMAN İÇERİK KONTROLÜ - OPPORTUNITY 6")
print("=" * 70)
print()

atts = db.query(OpportunityAttachment).filter(
    OpportunityAttachment.opportunity_id == 6,
    OpportunityAttachment.downloaded == True
).all()

total_chars = 0
total_words = 0

for att in atts:
    if att.local_path:
        path = Path(att.local_path)
        if path.exists():
            print(f"📄 {att.name} ({att.mime_type}):")
            print(f"   Path: {path.name}")
            print(f"   Size: {path.stat().st_size:,} bytes")
            
            # Analyze document
            result = analyze_document(str(path), att.mime_type)
            chars = result.get('text_length', 0)
            words = result.get('word_count', 0)
            tables = len(result.get('tables', []))
            
            print(f"   Extracted: {chars:,} chars, {words:,} words, {tables} tables")
            
            # Show preview
            text = result.get('extracted_text', '')
            if text:
                print(f"   Preview (ilk 200 karakter):")
                print(f"   {text[:200]}...")
            
            total_chars += chars
            total_words += words
            print()

print(f"📊 TOPLAM:")
print(f"   Total Chars: {total_chars:,}")
print(f"   Total Words: {total_words:,}")
print(f"   Expected in Analysis: 40,254 chars, 6,600 words")

db.close()


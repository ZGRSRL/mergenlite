#!/usr/bin/env python3
"""Check actual dates from documents for opportunity 6."""
import sys
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models import Opportunity, OpportunityAttachment
from app.services.parsing.document_analyzer import analyze_document
from pathlib import Path
import re

print("=" * 70)
print("📄 DÖKÜMANLARDAN TARİH KONTROLÜ - OPPORTUNITY 6")
print("=" * 70)
print()

db = SessionLocal()
opp = db.query(Opportunity).filter(Opportunity.id == 6).first()
if not opp:
    print("❌ Opportunity bulunamadı")
    exit(1)

print(f"📋 Opportunity: {opp.title}")
print(f"   Notice ID: {opp.notice_id}")
print()

# Get attachments
attachments = db.query(OpportunityAttachment).filter(
    OpportunityAttachment.opportunity_id == 6,
    OpportunityAttachment.downloaded == True
).all()

print(f"📎 Attachments: {len(attachments)}")
print()

# Check dates in each document
date_patterns = [
    r'\b(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12][0-9]|3[01])\b',  # YYYY-MM-DD
    r'\b(0[1-9]|1[0-2])[-/](0[1-9]|[12][0-9]|3[01])[-/](20\d{2})\b',  # MM-DD-YYYY
    r'\b(March|April|May|June|July|August|September|October|November|December|January|February)\s+(\d{1,2}),?\s+(20\d{2})\b',  # Month DD, YYYY
    r'\b(20\d{2})\s+(March|April|May|June|July|August|September|October|November|December|January|February)\s+(\d{1,2})\b',  # YYYY Month DD
]

all_dates = []

for att in attachments:
    print(f"📄 {att.name or 'Unknown'}")
    if att.local_path:
        file_path = Path(att.local_path)
        if not file_path.exists():
            # Try alternative paths
            alt_paths = [
                Path('/data') / att.local_path.lstrip('/'),
                Path('/data/opportunities') / opp.notice_id / 'attachments' / Path(att.local_path).name
            ]
            for alt_path in alt_paths:
                if alt_path.exists():
                    file_path = alt_path
                    break
        
        if file_path.exists():
            try:
                result = analyze_document(str(file_path))
                text = result.get('extracted_text', '')
                
                # Find dates in text
                dates_found = []
                for pattern in date_patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        date_str = match.group(0)
                        dates_found.append(date_str)
                
                if dates_found:
                    print(f"   📅 Tarihler bulundu: {len(dates_found)}")
                    # Show unique dates
                    unique_dates = list(set(dates_found))[:10]
                    for date in unique_dates:
                        print(f"      - {date}")
                        all_dates.append(date)
                else:
                    print(f"   ⚠️ Tarih bulunamadı")
                
                # Also check for "March 2025" or "2025" patterns
                year_pattern = r'\b(202[456])\b'
                years = re.findall(year_pattern, text)
                if years:
                    unique_years = list(set(years))
                    print(f"   📅 Yıllar: {', '.join(unique_years)}")
                
                # Check for specific date mentions
                if 'March' in text or 'march' in text:
                    march_matches = re.findall(r'March\s+(\d{1,2}),?\s+(20\d{2})', text, re.IGNORECASE)
                    if march_matches:
                        print(f"   📅 March tarihleri:")
                        for day, year in march_matches:
                            print(f"      - March {day}, {year}")
                
            except Exception as e:
                print(f"   ❌ Hata: {e}")
        else:
            print(f"   ⚠️ Dosya bulunamadı: {att.local_path}")
    print()

print("=" * 70)
print("📊 ÖZET:")
if all_dates:
    unique_dates = list(set(all_dates))
    print(f"   Toplam farklı tarih: {len(unique_dates)}")
    print(f"   Tarihler: {', '.join(unique_dates[:20])}")
else:
    print("   ⚠️ Hiç tarih bulunamadı")

print()
print("=" * 70)

db.close()


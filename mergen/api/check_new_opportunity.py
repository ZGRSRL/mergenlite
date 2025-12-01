#!/usr/bin/env python3
"""Check and add new opportunity from SAM.gov."""
import requests
import sys
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models import Opportunity
import json

API_BASE = "http://localhost:8000"
NOTICE_ID = "c2adb79f5ce84717bd0ccc8584809ac9"

db = SessionLocal()

# Check if opportunity exists
opp = db.query(Opportunity).filter(Opportunity.notice_id == NOTICE_ID).first()

if opp:
    print(f"✅ Opportunity found:")
    print(f"   ID: {opp.id}")
    print(f"   Title: {opp.title}")
    print(f"   Agency: {opp.agency}")
    print(f"   Status: {opp.status}")
    
    # Check latest analysis
    from app.models import AIAnalysisResult
    latest = db.query(AIAnalysisResult).filter(
        AIAnalysisResult.opportunity_id == opp.id
    ).order_by(AIAnalysisResult.created_at.desc()).first()
    
    if latest:
        print(f"\n📊 Latest Analysis:")
        print(f"   ID: {latest.id}")
        print(f"   Type: {latest.analysis_type}")
        print(f"   Status: {latest.status}")
        print(f"   PDF: {latest.pdf_path}")
        
        if latest.pdf_path:
            from pathlib import Path
            pdf = Path(latest.pdf_path)
            if pdf.exists():
                size = pdf.stat().st_size
                print(f"   PDF Size: {size:,} bytes")
                if size < 5000:
                    print(f"   ⚠️ PDF çok küçük - muhtemelen boş!")
            else:
                print(f"   ❌ PDF dosyası bulunamadı!")
    else:
        print(f"\n⚠️ Henüz analiz yapılmamış")
else:
    print(f"❌ Opportunity bulunamadı: {NOTICE_ID}")
    print(f"   Önce SAM.gov'dan fırsatı eklemelisiniz")

db.close()


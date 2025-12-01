#!/usr/bin/env python3
"""Reset attachments and force re-download for opportunity 6."""
import sys
sys.path.insert(0, '/app')

from app.db import SessionLocal
from app.models import OpportunityAttachment
from app.services.attachment_service import download_attachments_for_opportunity
import asyncio

db = SessionLocal()

print("=" * 70)
print("🔄 ATTACHMENT RESET VE YENİDEN İNDİRME - OPPORTUNITY 6")
print("=" * 70)
print()

# Step 1: Reset attachments
print("🔄 Step 1: Attachments reset ediliyor...")
atts = db.query(OpportunityAttachment).filter(OpportunityAttachment.opportunity_id == 6).all()
print(f"   Found {len(atts)} attachments")

for att in atts:
    print(f"   Resetting attachment {att.id}: {att.name}")
    att.downloaded = False
    att.local_path = None
    att.downloaded_at = None
    att.size_bytes = None

db.commit()
print("✅ Attachments reset edildi")
print()

# Step 2: Force re-download
print("📥 Step 2: Dokümanlar yeniden indiriliyor...")
try:
    result = asyncio.run(download_attachments_for_opportunity(db, 6, job_id=None))
    print(f"✅ Download completed!")
    print(f"   Result: {result}")
except Exception as e:
    print(f"❌ Download error: {e}")
    import traceback
    traceback.print_exc()

# Step 3: Verify
print("\n📋 Step 3: Dosyalar kontrol ediliyor...")
db.expire_all()
atts = db.query(OpportunityAttachment).filter(OpportunityAttachment.opportunity_id == 6).all()

from pathlib import Path
for att in atts:
    print(f"\nAttachment {att.id}:")
    print(f"   Name: {att.name}")
    print(f"   Downloaded: {att.downloaded}")
    print(f"   Path: {att.local_path}")
    
    if att.local_path:
        path = Path(att.local_path)
        if path.exists():
            print(f"   ✅ File exists: {path.stat().st_size:,} bytes")
        else:
            print(f"   ❌ File NOT found!")

db.close()


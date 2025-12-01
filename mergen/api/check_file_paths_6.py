from app.db import SessionLocal
from app.models import OpportunityAttachment
from pathlib import Path
import sys
sys.path.insert(0, '/app')

from app.services.pipeline_service import _resolve_attachment_path

db = SessionLocal()

print("=" * 70)
print("📁 DOSYA PATH KONTROLÜ - OPPORTUNITY 6")
print("=" * 70)
print()

atts = db.query(OpportunityAttachment).filter(OpportunityAttachment.opportunity_id == 6).all()

for att in atts:
    print(f"Attachment ID {att.id}:")
    print(f"  Name: {att.name}")
    print(f"  DB local_path: {att.local_path}")
    print(f"  Downloaded: {att.downloaded}")
    
    # Direct path check
    if att.local_path:
        direct_path = Path(att.local_path)
        print(f"  Direct path exists: {direct_path.exists()}")
        if direct_path.exists():
            print(f"  Direct path size: {direct_path.stat().st_size:,} bytes")
    
    # Resolved path check
    resolved = _resolve_attachment_path(att.local_path)
    if resolved:
        print(f"  Resolved path: {resolved}")
        print(f"  Resolved exists: {resolved.exists()}")
        if resolved.exists():
            print(f"  Resolved size: {resolved.stat().st_size:,} bytes")
    else:
        print(f"  Resolved: None")
    
    print()

# Check directory
opp_dir = Path("/data/opportunities/c2adb79f5ce84717bd0ccc8584809ac9/attachments")
print(f"Attachments directory: {opp_dir}")
print(f"Directory exists: {opp_dir.exists()}")
if opp_dir.exists():
    files = list(opp_dir.glob("*"))
    print(f"Files in directory: {len(files)}")
    for f in files:
        print(f"  - {f.name} ({f.stat().st_size:,} bytes)")

db.close()


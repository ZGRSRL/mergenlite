from app.db import SessionLocal
from app.models import OpportunityAttachment
from pathlib import Path

db = SessionLocal()

# Get attachments for opportunity 3
attachments = db.query(OpportunityAttachment).filter(
    OpportunityAttachment.opportunity_id == 3
).all()

print(f"Found {len(attachments)} attachments:\n")
for att in attachments:
    print(f"Attachment ID {att.id}:")
    print(f"  Name: {att.name}")
    print(f"  Downloaded: {att.downloaded}")
    print(f"  Local path: {att.local_path}")
    if att.local_path:
        path = Path(att.local_path)
        print(f"  Path exists: {path.exists()}")
        if not path.exists():
            # Try absolute path
            abs_path = Path("/data") / path if not path.is_absolute() else path
            print(f"  Absolute path exists: {abs_path.exists()}")
            if abs_path.exists():
                print(f"  ✅ Found at: {abs_path}")
    print()

db.close()


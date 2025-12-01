from app.db import SessionLocal
from app.models import OpportunityAttachment
import requests
import time

db = SessionLocal()

# Reset downloaded flags
attachments = db.query(OpportunityAttachment).filter(
    OpportunityAttachment.opportunity_id == 3
).all()

print(f"Resetting {len(attachments)} attachments...")
for att in attachments:
    att.downloaded = False
    att.local_path = None
    att.downloaded_at = None
    print(f"  Reset attachment {att.id}: {att.name}")

db.commit()
print("✅ Attachments reset")

# Trigger download
print("\nTriggering download...")
response = requests.post('http://localhost:8000/api/opportunities/3/download-attachments')
result = response.json()
job_id = result.get('job_id')
print(f"Job ID: {job_id}")

# Wait a bit
print("\nWaiting 15 seconds for download to start...")
time.sleep(15)

# Check if files exist
from pathlib import Path
import os

BASE_DATA_DIR = Path("/data")
opp_dir = BASE_DATA_DIR / "opportunities" / "97c450b7d3554a738d0d4de07ffa0e0a" / "attachments"
print(f"\nChecking directory: {opp_dir}")
print(f"Directory exists: {opp_dir.exists()}")

if opp_dir.exists():
    files = os.listdir(opp_dir)
    print(f"Files found: {len(files)}")
    for f in files:
        file_path = opp_dir / f
        size = file_path.stat().st_size if file_path.exists() else 0
        print(f"  - {f} ({size} bytes)")
else:
    print("❌ Directory does not exist!")

db.close()


#!/usr/bin/env python3
"""Sync new opportunity from SAM.gov URL and start analysis."""
import requests
import time
import re

API_BASE = "http://localhost:8000"
SAM_URL = "https://sam.gov/opp/97c450b7d3554a738d0d4de07ffa0e0a/view"

# Extract opportunity ID from URL
opp_id_match = re.search(r"/opp/([0-9a-fA-F]{32})", SAM_URL)
if not opp_id_match:
    print(f"ERROR: Could not extract opportunity ID from URL: {SAM_URL}")
    exit(1)

opportunity_id = opp_id_match.group(1)
print(f"Extracted Opportunity ID: {opportunity_id}")
print(f"URL: {SAM_URL}\n")

# Step 1: Sync opportunity from SAM.gov
print("Step 1: Syncing opportunity from SAM.gov...")
# Try to sync using the opportunity ID
# First, check if it already exists
resp = requests.get(f"{API_BASE}/api/opportunities", params={"notice_id": opportunity_id})
existing = resp.json()
if existing and len(existing) > 0:
    opp = existing[0]
    print(f"✓ Opportunity already exists: ID {opp['id']}, Title: {opp.get('title', 'N/A')}")
    opportunity_db_id = opp['id']
else:
    # Need to sync - try using SAM.gov sync endpoint
    print("Opportunity not found, attempting sync...")
    # Use sync endpoint with opportunity_id parameter
    resp = requests.post(
        f"{API_BASE}/api/opportunities/sync",
        params={"opportunity_id": opportunity_id, "limit": 1}
    )
    if resp.status_code == 200:
        sync_result = resp.json()
        print(f"✓ Sync completed: {sync_result.get('message', 'OK')}")
        # Get the synced opportunity
        resp = requests.get(f"{API_BASE}/api/opportunities", params={"notice_id": opportunity_id})
        existing = resp.json()
        if existing and len(existing) > 0:
            opp = existing[0]
            opportunity_db_id = opp['id']
            print(f"✓ Opportunity synced: ID {opportunity_db_id}, Title: {opp.get('title', 'N/A')}")
        else:
            print("ERROR: Opportunity not found after sync")
            exit(1)
    else:
        print(f"ERROR: Sync failed: {resp.status_code} - {resp.text}")
        exit(1)

print()

# Step 2: Check attachments
print("Step 2: Checking attachments...")
resp = requests.get(f"{API_BASE}/api/opportunities/{opportunity_db_id}/attachments")
attachments = resp.json()
print(f"Found {len(attachments)} attachment(s)")
for i, att in enumerate(attachments, 1):
    print(f"  {i}. {att.get('name')} - Downloaded: {att.get('downloaded')}")
print()

# Step 3: Download attachments if needed
if attachments and not all(att.get('downloaded') for att in attachments):
    print("Step 3: Downloading attachments...")
    resp = requests.post(f"{API_BASE}/api/opportunities/{opportunity_db_id}/attachments/download")
    if resp.status_code == 200:
        download_result = resp.json()
        print(f"✓ Download job started: {download_result.get('job_id', 'N/A')}")
        # Wait for download to complete
        job_id = download_result.get('job_id')
        if job_id:
            print("Waiting for download to complete...")
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                resp = requests.get(f"{API_BASE}/api/opportunities/download/jobs/{job_id}")
                if resp.status_code == 200:
                    job = resp.json()
                    status = job.get('status')
                    print(f"  Download status: {status} ({i+1}s)")
                    if status in ['completed', 'failed']:
                        break
    else:
        print(f"WARNING: Download failed: {resp.status_code}")
print()

# Step 4: Start SOW analysis
print("Step 4: Starting SOW analysis...")
resp = requests.post(
    f"{API_BASE}/api/pipeline/run",
    json={"opportunity_id": opportunity_db_id, "analysis_type": "sow"}
)
if resp.status_code == 200:
    result = resp.json()
    analysis_id = result.get("analysis_result_id")
    print(f"✓ SOW Analysis started: ID {analysis_id}")
    
    # Wait for analysis to complete
    print("Waiting for analysis to complete...")
    for i in range(60):  # Wait up to 60 seconds
        time.sleep(2)
        resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
        if resp.status_code == 200:
            result = resp.json()
            status = result.get('status')
            print(f"  Analysis status: {status} ({i*2}s)")
            if status in ['completed', 'failed']:
                break
    
    # Check results
    print("\n=== Analysis Results ===")
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
    if resp.status_code == 200:
        result = resp.json()
        result_json = result.get('result_json', {})
        if isinstance(result_json, str):
            import json
            result_json = json.loads(result_json)
        
        docs = result_json.get('analyzed_documents', [])
        print(f"Analyzed Documents: {len(docs)}")
        total_chars = 0
        for i, doc in enumerate(docs, 1):
            text_len = doc.get('text_length', 0)
            total_chars += text_len
            print(f"  Doc {i}: {doc.get('attachment_name', 'N/A')} - {text_len} chars")
            if text_len < 100 and text_len > 0:
                print(f"    Content: {repr(doc.get('extracted_text', '')[:200])}")
        
        print(f"\nTotal extracted text: {total_chars} characters")
        
        if total_chars > 1000:
            print("✓ SUCCESS: Substantial text extracted!")
        elif total_chars > 0:
            print("⚠ WARNING: Very little text extracted")
        else:
            print("✗ ERROR: No text extracted")
else:
    print(f"ERROR: Failed to start analysis: {resp.status_code} - {resp.text}")


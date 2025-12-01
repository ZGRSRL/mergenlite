#!/usr/bin/env python3
"""Start new SOW analysis and monitor logs."""
import requests
import time

API_BASE = "http://localhost:8000"

print("Starting new SOW analysis for opportunity 1...")
resp = requests.post(f"{API_BASE}/api/pipeline/run", json={"opportunity_id": 1, "analysis_type": "sow"})
print(f"Response status: {resp.status_code}")
if resp.status_code != 200:
    print(f"Error: {resp.text}")
    exit(1)
result = resp.json()
analysis_id = result.get("analysis_result_id")
print(f"New SOW Analysis ID: {analysis_id}")

print("\nWaiting 15 seconds for processing...")
time.sleep(15)

print("\nChecking analysis result...")
resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
result = resp.json()
print(f"Status: {result.get('status')}")

# Check extracted text
result_json = result.get("result_json", {})
if isinstance(result_json, str):
    import json
    result_json = json.loads(result_json)

docs = result_json.get("analyzed_documents", [])
print(f"\nAnalyzed Documents: {len(docs)}")
for i, doc in enumerate(docs, 1):
    text_len = doc.get("text_length", 0)
    print(f"  Doc {i}: {doc.get('attachment_name', 'N/A')} - {text_len} chars")
    if text_len < 100:
        print(f"    Content: {repr(doc.get('extracted_text', '')[:200])}")


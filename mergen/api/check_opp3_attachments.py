#!/usr/bin/env python3
"""Check opportunity 3 attachments in detail."""
import requests
from pathlib import Path
from app.services.parsing.pdf_utils import extract_text_from_pdf

API_BASE = "http://localhost:8000"
OPP_ID = 3

print(f"=== Opportunity {OPP_ID} Attachments ===\n")

resp = requests.get(f"{API_BASE}/api/opportunities/{OPP_ID}/attachments")
atts = resp.json()

print(f"Total attachments: {len(atts)}\n")

for i, att in enumerate(atts, 1):
    print(f"{i}. {att.get('name')}")
    print(f"   ID: {att.get('id')}")
    print(f"   Downloaded: {att.get('downloaded')}")
    print(f"   MIME Type: {att.get('mime_type', 'N/A')}")
    print(f"   Size: {att.get('size_bytes', 'N/A')} bytes")
    path = att.get('local_path')
    if path:
        path_obj = Path(path)
        print(f"   Path: {path}")
        if path_obj.exists():
            print(f"   File exists: Yes")
            print(f"   File size: {path_obj.stat().st_size} bytes")
            
            # Try to extract text
            if path.endswith('.pdf'):
                print(f"   Testing PDF extraction...")
                try:
                    text = extract_text_from_pdf(str(path))
                    print(f"   Extracted: {len(text)} chars")
                    if len(text) > 50:
                        print(f"   First 500 chars:\n{text[:500]}\n")
                    elif text:
                        print(f"   Content: {repr(text)}\n")
                    else:
                        print(f"   No text extracted\n")
                except Exception as e:
                    print(f"   Error: {e}\n")
        else:
            print(f"   File exists: NO\n")
    print()


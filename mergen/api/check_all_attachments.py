#!/usr/bin/env python3
"""Check all attachments for opportunity 1."""
import requests
from pathlib import Path
from app.services.parsing.pdf_utils import extract_text_from_pdf

API_BASE = "http://localhost:8000"

resp = requests.get(f"{API_BASE}/api/opportunities/1/attachments")
atts = resp.json()

print(f"=== Total Attachments: {len(atts)} ===\n")

for i, att in enumerate(atts, 1):
    print(f"{i}. {att.get('name')}")
    print(f"   Downloaded: {att.get('downloaded')}")
    path = att.get('local_path')
    if path:
        path_obj = Path(path)
        if path_obj.exists():
            print(f"   Path: {path}")
            print(f"   Size: {path_obj.stat().st_size} bytes")
            
            # Try to extract text
            if path.endswith('.pdf'):
                try:
                    text = extract_text_from_pdf(str(path))
                    print(f"   Extracted text: {len(text)} chars")
                    if len(text) > 50:
                        print(f"   First 200 chars: {text[:200]}")
                    elif text:
                        print(f"   Content: {repr(text)}")
                except Exception as e:
                    print(f"   Error extracting: {e}")
        else:
            print(f"   Path: {path} (NOT FOUND)")
    print()


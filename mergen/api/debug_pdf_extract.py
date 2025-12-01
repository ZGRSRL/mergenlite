#!/usr/bin/env python3
"""PDF extract debug - neden sadece 16 karakter?"""
from pathlib import Path
import requests
import json

API_BASE = "http://localhost:8000"

# Get attachments
print("=== Attachment Listesi ===\n")
resp = requests.get(f"{API_BASE}/api/opportunities/1/attachments")
atts = resp.json()
for i, att in enumerate(atts[:5], 1):
    print(f"{i}. {att.get('name')}")
    print(f"   Downloaded: {att.get('downloaded')}")
    print(f"   Local Path: {att.get('local_path', 'N/A')}")
    print(f"   MIME Type: {att.get('mime_type', 'N/A')}")
    print()

# Test PDF extraction directly
if atts:
    att = atts[0]
    pdf_path = att.get('local_path')
    
    if pdf_path:
        print(f"=== PDF Extract Test: {Path(pdf_path).name} ===\n")
        
        # Check if file exists
        path_obj = Path(pdf_path)
        if not path_obj.exists():
            # Try alternative paths
            alt_paths = [
                Path('/data') / pdf_path.lstrip('/'),
                Path('/app/data') / pdf_path.lstrip('/'),
            ]
            for alt_path in alt_paths:
                if alt_path.exists():
                    pdf_path = str(alt_path)
                    path_obj = alt_path
                    print(f"Found at alternative path: {pdf_path}\n")
                    break
        
        if path_obj.exists():
            print(f"File exists: Yes")
            print(f"File size: {path_obj.stat().st_size} bytes")
            print(f"File extension: {path_obj.suffix}\n")
            
            # Test extraction
            try:
                from app.services.parsing.pdf_utils import extract_text_from_pdf
                print("Testing extract_text_from_pdf...")
                text = extract_text_from_pdf(pdf_path)
                print(f"Extracted text length: {len(text)} characters")
                print(f"Extracted word count: {len(text.split())} words")
                print(f"\nFirst 1000 characters:")
                print(text[:1000])
                print(f"\nLast 500 characters:")
                print(text[-500:] if len(text) > 500 else text)
            except Exception as e:
                print(f"Error during extraction: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"File NOT found at: {pdf_path}")
            print("Trying to find file...")
            # Search in common locations
            base_paths = [
                Path('/data'),
                Path('/app/data'),
                Path('/app'),
            ]
            for base in base_paths:
                if base.exists():
                    for pdf_file in base.rglob('*.pdf'):
                        if '6b975417' in str(pdf_file) or 'download' in pdf_file.name:
                            print(f"Found potential file: {pdf_file}")
                            print(f"  Size: {pdf_file.stat().st_size} bytes")
                            try:
                                from app.services.parsing.pdf_utils import extract_text_from_pdf
                                text = extract_text_from_pdf(str(pdf_file))
                                print(f"  Extracted: {len(text)} chars")
                                if len(text) > 100:
                                    print(f"  First 500: {text[:500]}")
                            except Exception as e:
                                print(f"  Error: {e}")
                            break


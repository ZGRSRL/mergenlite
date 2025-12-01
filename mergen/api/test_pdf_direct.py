#!/usr/bin/env python3
"""PDF'i direkt test et."""
import pdfplumber
import fitz
from pathlib import Path

pdf_path = Path('/data/opportunities/6b975417d0f44a0c959a5c08d25dc18b/attachments/6b975417d0f44a0c959a5c08d25dc18b_12_download.pdf')

print("=== PDF Direct Test ===\n")

if not pdf_path.exists():
    print(f"PDF NOT FOUND: {pdf_path}")
    exit(1)

print(f"PDF Path: {pdf_path}")
print(f"Size: {pdf_path.stat().st_size} bytes\n")

# Test 1: pdfplumber
print("1. pdfplumber test:")
try:
    with pdfplumber.open(str(pdf_path)) as pdf:
        print(f"   Pages: {len(pdf.pages)}")
        all_text = ""
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            all_text += page_text + "\n"
            print(f"   Page {i+1}: {len(page_text)} chars")
            
            # Check for tables
            tables = page.extract_tables()
            if tables:
                print(f"   Page {i+1} has {len(tables)} table(s)")
        
        print(f"   Total text: {len(all_text)} chars")
        if len(all_text) > 50:
            print(f"   First 500 chars:\n{all_text[:500]}\n")
        else:
            print(f"   Text: {repr(all_text)}\n")
except Exception as e:
    print(f"   Error: {e}\n")

# Test 2: PyMuPDF
print("2. PyMuPDF (fitz) test:")
try:
    doc = fitz.open(str(pdf_path))
    print(f"   Pages: {doc.page_count}")
    all_text = ""
    for i in range(doc.page_count):
        page = doc[i]
        page_text = page.get_text()
        all_text += page_text + "\n"
        print(f"   Page {i+1}: {len(page_text)} chars")
    doc.close()
    print(f"   Total text: {len(all_text)} chars")
    if len(all_text) > 50:
        print(f"   First 500 chars:\n{all_text[:500]}\n")
    else:
        print(f"   Text: {repr(all_text)}\n")
except Exception as e:
    print(f"   Error: {e}\n")

# Test 3: Check if PDF is image-based
print("3. PDF structure check:")
try:
    doc = fitz.open(str(pdf_path))
    print(f"   Page count: {doc.page_count}")
    for i in range(min(3, doc.page_count)):
        page = doc[i]
        # Check for images
        image_list = page.get_images()
        print(f"   Page {i+1}: {len(image_list)} image(s)")
        
        # Check text blocks
        blocks = page.get_text("blocks")
        text_blocks = [b for b in blocks if b[6] == 0]  # 0 = text, 1 = image
        print(f"   Page {i+1}: {len(text_blocks)} text block(s)")
        
        if len(image_list) > 0 and len(text_blocks) == 0:
            print(f"   ⚠️ Page {i+1} appears to be image-only (scanned PDF)")
    doc.close()
except Exception as e:
    print(f"   Error: {e}")


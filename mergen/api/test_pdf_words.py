#!/usr/bin/env python3
"""PDF word extraction test."""
import pdfplumber
from pathlib import Path

pdf_path = Path('/data/opportunities/6b975417d0f44a0c959a5c08d25dc18b/attachments/6b975417d0f44a0c959a5c08d25dc18b_12_download.pdf')

print("=== PDF Word Extraction Test ===\n")

if not pdf_path.exists():
    print(f"PDF NOT FOUND: {pdf_path}")
    exit(1)

print(f"PDF: {pdf_path.name}")
print(f"Size: {pdf_path.stat().st_size} bytes\n")

with pdfplumber.open(str(pdf_path)) as pdf:
    print(f"Total Pages: {len(pdf.pages)}\n")
    
    for i, page in enumerate(pdf.pages):
        print(f"Page {i+1}:")
        
        # Method 1: extract_text()
        text1 = page.extract_text() or ""
        print(f"  extract_text(): {len(text1)} chars")
        if text1:
            print(f"    Content: {repr(text1[:100])}")
        
        # Method 2: extract_words()
        words = page.extract_words()
        print(f"  extract_words(): {len(words)} words")
        if words:
            text2 = " ".join([w.get("text", "") for w in words if w.get("text")])
            print(f"    Reconstructed: {len(text2)} chars")
            if text2 and len(text2) > len(text1):
                print(f"    Content: {text2[:200]}")
        
        # Method 3: Check for tables
        tables = page.extract_tables()
        if tables:
            print(f"  Tables: {len(tables)} found")
            for t_idx, table in enumerate(tables):
                print(f"    Table {t_idx+1}: {len(table)} rows")
        
        print()


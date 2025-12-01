import pdfplumber
from pathlib import Path

# Test PDF 1
pdf1_path = '/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/attachments/97c450b7d3554a738d0d4de07ffa0e0a_1_download.pdf'
print(f"Testing PDF 1: {Path(pdf1_path).stat().st_size} bytes")
with pdfplumber.open(pdf1_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    total_text = ""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        total_text += text
        print(f"Page {i+1}: {len(text)} chars")
    print(f"Total: {len(total_text)} chars, {len(total_text.split())} words")
    print(f"First 200 chars: {total_text[:200]}")

print("\n" + "="*50 + "\n")

# Test PDF 3
pdf3_path = '/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/attachments/97c450b7d3554a738d0d4de07ffa0e0a_3_download.pdf'
print(f"Testing PDF 3: {Path(pdf3_path).stat().st_size} bytes")
with pdfplumber.open(pdf3_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    total_text = ""
    for i, page in enumerate(pdf.pages):
        text = page.extract_text() or ""
        total_text += text
        print(f"Page {i+1}: {len(text)} chars")
    print(f"Total: {len(total_text)} chars, {len(total_text.split())} words")
    print(f"First 200 chars: {total_text[:200]}")

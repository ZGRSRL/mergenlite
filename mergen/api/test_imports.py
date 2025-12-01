#!/usr/bin/env python3
"""Test PDF utils imports."""
try:
    import pdfplumber
    print("✓ pdfplumber: OK")
except Exception as e:
    print(f"✗ pdfplumber: FAILED - {e}")

try:
    import fitz
    print("✓ PyMuPDF (fitz): OK")
except Exception as e:
    print(f"✗ PyMuPDF: FAILED - {e}")

try:
    import camelot
    print("✓ camelot: OK")
except Exception as e:
    print(f"✗ camelot: FAILED - {e}")

try:
    from app.services.parsing.pdf_utils import extract_text_from_pdf
    print("✓ pdf_utils import: OK")
except Exception as e:
    print(f"✗ pdf_utils import: FAILED - {e}")
    import traceback
    traceback.print_exc()


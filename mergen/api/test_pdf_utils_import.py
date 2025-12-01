#!/usr/bin/env python3
"""Test pdf_utils import."""
import sys
sys.path.insert(0, '/app')

try:
    from app.services.parsing.pdf_utils import extract_text_from_pdf
    print("✓ Direct import: OK")
except Exception as e:
    print(f"✗ Direct import: FAILED - {e}")
    import traceback
    traceback.print_exc()

try:
    from app.services.parsing import pdf_utils
    print("✓ Module import: OK")
    print(f"  Has extract_text_from_pdf: {hasattr(pdf_utils, 'extract_text_from_pdf')}")
    if hasattr(pdf_utils, 'extract_text_from_pdf'):
        print("  ✓ Function exists")
    else:
        print("  ✗ Function missing")
except Exception as e:
    print(f"✗ Module import: FAILED - {e}")
    import traceback
    traceback.print_exc()

try:
    from app.services.parsing.document_analyzer import PDF_UTILS_AVAILABLE
    print(f"✓ document_analyzer import: OK")
    print(f"  PDF_UTILS_AVAILABLE: {PDF_UTILS_AVAILABLE}")
except Exception as e:
    print(f"✗ document_analyzer import: FAILED - {e}")
    import traceback
    traceback.print_exc()


#!/usr/bin/env python3
"""Test relative import in document_analyzer."""
import sys
sys.path.insert(0, '/app')

# Simulate what document_analyzer.py does
import logging
logger = logging.getLogger(__name__)

print("Testing relative import...")
try:
    # This is what document_analyzer.py does
    from app.services.parsing.pdf_utils import extract_text_from_pdf, extract_tables_from_pdf, extract_metadata_from_pdf
    print("✓ Absolute import: OK")
    PDF_UTILS_AVAILABLE = True
except ImportError as e:
    print(f"✗ Absolute import: FAILED - {e}")
    PDF_UTILS_AVAILABLE = False
    import traceback
    traceback.print_exc()

print(f"\nPDF_UTILS_AVAILABLE: {PDF_UTILS_AVAILABLE}")

# Now test relative import (what document_analyzer.py actually uses)
print("\nTesting relative import (from .pdf_utils)...")
try:
    # This simulates being inside the parsing package
    import app.services.parsing as parsing_pkg
    from app.services.parsing.pdf_utils import extract_text_from_pdf
    print("✓ Relative import via package: OK")
except ImportError as e:
    print(f"✗ Relative import: FAILED - {e}")
    import traceback
    traceback.print_exc()


#!/usr/bin/env python3
"""Final test of analyze_document."""
import sys
sys.path.insert(0, '/app')

from app.services.parsing.document_analyzer import PDF_UTILS_AVAILABLE, analyze_document
from pathlib import Path

print(f"PDF_UTILS_AVAILABLE: {PDF_UTILS_AVAILABLE}")

path = Path('/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/attachments/97c450b7d3554a738d0d4de07ffa0e0a_1_download.pdf')
print(f"Path exists: {path.exists()}")
print(f"Path: {path}")

result = analyze_document(str(path), 'application/pdf')
print(f"Text length: {result.get('text_length', 0)}")
print(f"Word count: {result.get('word_count', 0)}")
print(f"Error: {result.get('error')}")
print(f"Document type: {result.get('document_type')}")

if result.get('text_length', 0) > 0:
    print(f"\nFirst 500 chars:\n{result.get('extracted_text', '')[:500]}")


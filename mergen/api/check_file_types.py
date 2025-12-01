#!/usr/bin/env python3
"""Check file types of downloaded attachments."""
from pathlib import Path

att_dir = Path('/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/attachments')
files = list(att_dir.glob('*.bin'))

print("File types:")
for f in files:
    # Read first few bytes to determine type
    with open(f, 'rb') as file:
        header = file.read(16)
        file_type = "unknown"
        if header.startswith(b'%PDF'):
            file_type = "PDF"
        elif header.startswith(b'PK\x03\x04'):
            file_type = "ZIP/DOCX/XLSX"
        elif header.startswith(b'\xd0\xcf\x11\xe0'):
            file_type = "MS Office (old)"
        print(f"{f.name}: {file_type} ({f.stat().st_size} bytes)")


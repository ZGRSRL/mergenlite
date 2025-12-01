import pdfplumber
from pathlib import Path

# Test PDF 1 with tables
pdf1_path = '/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/attachments/97c450b7d3554a738d0d4de07ffa0e0a_1_download.pdf'
print(f"Testing PDF 1 with tables: {Path(pdf1_path).stat().st_size} bytes")
with pdfplumber.open(pdf1_path) as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    total_text = ""
    total_tables = 0
    for i, page in enumerate(pdf.pages):
        # Extract text
        text = page.extract_text() or ""
        total_text += text
        
        # Extract tables
        tables = page.extract_tables()
        if tables:
            total_tables += len(tables)
            print(f"Page {i+1}: {len(text)} chars, {len(tables)} table(s)")
            # Add table text
            for table_idx, table in enumerate(tables):
                table_text = "\n[TABLE " + str(table_idx + 1) + "]\n"
                for row in table:
                    clean_row = [str(cell) if cell is not None else "" for cell in row]
                    table_text += " | ".join(clean_row) + "\n"
                total_text += table_text
        else:
            print(f"Page {i+1}: {len(text)} chars, 0 tables")
    
    print(f"\nTotal: {len(total_text)} chars, {len(total_text.split())} words")
    print(f"Total tables found: {total_tables}")
    if total_tables > 0:
        print(f"✅ Found {total_tables} tables - this should increase word count significantly!")


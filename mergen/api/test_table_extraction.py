from app.services.parsing.pdf_utils import extract_tables_from_pdf

# Test table extraction
pdf_path = '/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/attachments/97c450b7d3554a738d0d4de07ffa0e0a_1_download.pdf'
tables = extract_tables_from_pdf(pdf_path)
print(f'Tables found by extract_tables_from_pdf: {len(tables)}')
if tables:
    print(f'First table has {len(tables[0])} rows')
    if tables[0]:
        print(f'First row: {tables[0][0]}')
else:
    print('❌ No tables extracted!')


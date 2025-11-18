# Sample Documents

This directory contains sample documents for testing the ZgrBid system.

## Required Files

Place the following sample files in this directory:

1. **rfq.pdf** - Sample RFQ document (e.g., AQD Seminar RFQ)
2. **sow.pdf** - Statement of Work document
3. **facility.pdf** - Facility technical specifications (e.g., DoubleTree hotel specs)
4. **past_performance.pdf** - Past performance portfolio
5. **pricing.xlsx** - Pricing spreadsheet with room rates, AV costs, etc.

## Sample Data

The system will automatically process these files when you run the demo. Make sure the files are named exactly as specified above.

## File Formats

- **PDF files**: Should contain text that can be extracted (not scanned images)
- **Excel files**: Should have clear column headers and pricing data
- **File sizes**: Keep under 10MB for optimal performance

## Testing

After placing the sample files, run:

```bash
make seed
```

This will process the files and create demo data in the database.




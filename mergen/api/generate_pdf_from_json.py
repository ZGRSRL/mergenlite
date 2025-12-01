#!/usr/bin/env python3
"""Generate PDF from analysis JSON file."""
import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.services.pdf_generator import generate_analysis_pdf

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_pdf_from_json.py <json_file> [output_pdf]")
        sys.exit(1)
    
    json_file = Path(sys.argv[1])
    if not json_file.exists():
        print(f"Error: JSON file not found: {json_file}")
        sys.exit(1)
    
    output_pdf = Path(sys.argv[2]) if len(sys.argv) > 2 else json_file.with_suffix('.pdf')
    
    # Load JSON (handle UTF-8 BOM if present)
    with open(json_file, 'r', encoding='utf-8-sig') as f:
        analysis_result = json.load(f)
    
    # Extract opportunity data
    opportunity = analysis_result.get('opportunity', {})
    
    print(f"Generating PDF from {json_file}...")
    print(f"Output: {output_pdf}")
    print(f"Opportunity: {opportunity.get('title', 'N/A')}")
    
    # Generate PDF
    success = generate_analysis_pdf(output_pdf, analysis_result, opportunity)
    
    if success:
        print(f"✓ PDF generated successfully: {output_pdf}")
    else:
        print("✗ PDF generation failed")
        sys.exit(1)

if __name__ == '__main__':
    main()


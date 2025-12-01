#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')

import requests
from pathlib import Path
from app.services.pdf_generator import generate_analysis_pdf
import json

# Get SOW analysis result
result = requests.get('http://localhost:8000/api/pipeline/results/147').json()
print("=== Regenerating SOW PDF with Hotel Match Results ===")
print(f"Status: {result['status']}")

# Get JSON content
json_content = result.get('result_json')
if isinstance(json_content, str):
    analysis_data = json.loads(json_content)
else:
    analysis_data = json_content

# Get opportunity data
opportunity_data = {
    "id": analysis_data.get('opportunity', {}).get('id'),
    "notice_id": analysis_data.get('opportunity', {}).get('notice_id'),
    "title": analysis_data.get('opportunity', {}).get('title'),
    "agency": analysis_data.get('opportunity', {}).get('agency'),
}

# Get hotel match results for this opportunity
opportunity_id = opportunity_data.get('id')
if opportunity_id:
    hotel_results = requests.get(f'http://localhost:8000/api/pipeline/opportunity/{opportunity_id}/results?limit=10').json()
    hotel_match = None
    for hr in hotel_results:
        if hr.get('analysis_type') == 'hotel_match' and hr.get('status') == 'completed':
            hotel_match = hr
            break
    
    if hotel_match:
        hotel_data = hotel_match.get('result_json')
        if isinstance(hotel_data, str):
            hotel_data = json.loads(hotel_data)
        
        # Add hotels to analysis_data
        analysis_data["hotels"] = hotel_data.get("hotels", [])
        analysis_data["hotel_search_criteria"] = hotel_data.get("requirements", {})
        analysis_data["related_hotels"] = hotel_data.get("hotels", [])
        print(f"\nAdded {len(analysis_data.get('hotels', []))} hotels from hotel match result {hotel_match.get('id')}")
    else:
        print("\nNo completed hotel match results found")

# Generate PDF
pdf_path = Path('/data/opportunities/97c450b7d3554a738d0d4de07ffa0e0a/outputs/analysis_147_detailed.pdf')
success = generate_analysis_pdf(pdf_path, analysis_data, opportunity_data)

if success:
    print(f"\n[OK] PDF regenerated: {pdf_path}")
    print(f"File size: {pdf_path.stat().st_size} bytes")
else:
    print("\n[X] PDF generation failed")


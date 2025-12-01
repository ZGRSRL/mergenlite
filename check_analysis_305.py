#!/usr/bin/env python3
"""Check Analysis #305 - SOW Analysis PDF issue."""
import sys
import requests
import json
from pathlib import Path

API_BASE = "http://localhost:8000"
ANALYSIS_ID = 305

print("=" * 70)
print(f"CHECKING ANALYSIS #{ANALYSIS_ID} - SOW Analysis")
print("=" * 70)
print()

try:
    # Get analysis result
    resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}")
    if resp.status_code == 200:
        result = resp.json()
        print(f"Status: {result.get('status')}")
        print(f"Analysis Type: {result.get('analysis_type')}")
        print(f"Created: {result.get('created_at')}")
        print(f"Completed: {result.get('completed_at')}")
        print()
        
        # Check PDF path
        pdf_path = result.get('pdf_path')
        if pdf_path:
            print(f"PDF Path: {pdf_path}")
            pdf_file = Path(pdf_path)
            if pdf_file.exists():
                size = pdf_file.stat().st_size
                print(f"PDF Size: {size:,} bytes")
                if size < 5000:
                    print(f"   [WARNING] PDF çok küçük - muhtemelen boş!")
                else:
                    print(f"   [OK] PDF dosyası mevcut")
            else:
                print(f"   [ERROR] PDF dosyası bulunamadı!")
        else:
            print(f"   [ERROR] PDF path yok!")
        print()
        
        # Check result_json
        result_json = result.get('result_json', {})
        if isinstance(result_json, str):
            try:
                result_json = json.loads(result_json) if result_json else {}
            except:
                result_json = {}
        
        print(f"Result JSON keys: {list(result_json.keys()) if result_json else 'Empty'}")
        
        # Check document analysis
        doc_analysis = result_json.get('document_analysis', {})
        if doc_analysis:
            print(f"\nDocument Analysis:")
            print(f"   Documents analyzed: {doc_analysis.get('documents_analyzed', 0)}")
            print(f"   Total text length: {doc_analysis.get('total_text_length', 0)}")
            print(f"   Total word count: {doc_analysis.get('total_word_count', 0)}")
        else:
            print(f"\n   [WARNING] Document analysis yok!")
        
        # Check SOW analysis
        sow_analysis = result_json.get('sow_analysis', {})
        if sow_analysis:
            print(f"\nSOW Analysis keys: {list(sow_analysis.keys())}")
            if not sow_analysis or len(sow_analysis) == 0:
                print(f"   [WARNING] SOW analysis boş!")
        else:
            print(f"\n   [WARNING] SOW analysis yok!")
        
        # Check logs for errors
        print(f"\nChecking logs...")
        logs_resp = requests.get(f"{API_BASE}/api/pipeline/results/{ANALYSIS_ID}/logs")
        if logs_resp.status_code == 200:
            logs = logs_resp.json()
            error_logs = [log for log in logs if log.get('level') == 'ERROR']
            warning_logs = [log for log in logs if log.get('level') == 'WARNING']
            
            print(f"   Total logs: {len(logs)}")
            print(f"   Errors: {len(error_logs)}")
            print(f"   Warnings: {len(warning_logs)}")
            
            if error_logs:
                print(f"\n   Recent Errors:")
                for log in error_logs[-5:]:
                    print(f"      - {log.get('message', 'N/A')[:200]}")
            
            if warning_logs:
                print(f"\n   Recent Warnings:")
                for log in warning_logs[-5:]:
                    print(f"      - {log.get('message', 'N/A')[:200]}")
        else:
            print(f"   Failed to get logs: {logs_resp.status_code}")
    else:
        print(f"Failed to get analysis: {resp.status_code}")
        print(resp.text)
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)


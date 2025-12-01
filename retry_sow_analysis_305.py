#!/usr/bin/env python3
"""Retry SOW Analysis for opportunity 38 (FIFA World Cup)."""
import sys
import requests
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

mergen_api = project_root / "mergen" / "api"
sys.path.insert(0, str(mergen_api))

API_BASE = "http://localhost:8000"
OPP_DB_ID = 38  # FIFA World Cup opportunity

print("=" * 70)
print("RETRY SOW ANALYSIS - Opportunity 38")
print("=" * 70)
print()

# Start SOW analysis
print("Starting SOW analysis...")
try:
    pipeline_resp = requests.post(
        f"{API_BASE}/api/pipeline/run",
        json={
            "opportunity_id": OPP_DB_ID,
            "analysis_type": "sow_draft",
            "pipeline_version": "v1",
            "options": {
                "max_text_length": 120000
            }
        }
    )
    
    if pipeline_resp.status_code == 200:
        result = pipeline_resp.json()
        analysis_id = result.get("analysis_result_id")
        print(f"   [OK] Analysis started!")
        print(f"      Analysis ID: {analysis_id}")
        print(f"      Status: {result.get('status')}")
        print()
        
        # Wait for completion
        print(f"Waiting for analysis to complete...")
        print(f"   (This may take 3-5 minutes)")
        print()
        
        max_wait = 300  # 5 minutes
        for i in range(max_wait):
            time.sleep(2)
            status_resp = requests.get(f"{API_BASE}/api/pipeline/results/{analysis_id}")
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                status = status_data.get('status')
                
                # Show progress every 10 seconds
                if i % 5 == 0:
                    print(f"   Status: {status} ({i*2}s)", end='\r')
                
                if status == 'completed':
                    print(f"\n   [OK] Analysis completed!")
                    
                    # Check PDF
                    pdf_path = status_data.get('pdf_path')
                    if pdf_path:
                        print(f"\n   PDF Path: {pdf_path}")
                        from pathlib import Path
                        pdf_file = Path(pdf_path)
                        if pdf_file.exists():
                            size = pdf_file.stat().st_size
                            print(f"   PDF Size: {size:,} bytes")
                            if size > 5000:
                                print(f"   [OK] PDF oluşturuldu ve boş değil!")
                            else:
                                print(f"   [WARNING] PDF çok küçük - muhtemelen boş!")
                        else:
                            print(f"   [ERROR] PDF dosyası bulunamadı!")
                    else:
                        print(f"   [WARNING] PDF path yok!")
                    
                    # Check SOW analysis
                    result_json = status_data.get('result_json', {})
                    if isinstance(result_json, str):
                        import json
                        result_json = json.loads(result_json) if result_json else {}
                    
                    sow_analysis = result_json.get('sow_analysis', {})
                    if sow_analysis and 'error' not in sow_analysis:
                        print(f"\n   [OK] SOW analysis başarılı!")
                        print(f"      Keys: {list(sow_analysis.keys())[:10]}")
                    else:
                        print(f"\n   [WARNING] SOW analysis hala boş veya hatalı!")
                        if 'error' in sow_analysis:
                            print(f"      Error: {sow_analysis.get('error')}")
                    
                    break
                elif status == 'failed':
                    print(f"\n   [FAILED] Analysis failed!")
                    error_msg = status_data.get('error_message', 'Unknown error')
                    print(f"      Error: {error_msg}")
                    break
        else:
            print(f"\n   [TIMEOUT] Analysis did not complete within {max_wait*2} seconds")
    else:
        print(f"   [ERROR] Failed to start analysis: {pipeline_resp.status_code}")
        print(f"      Response: {pipeline_resp.text}")
        
except Exception as e:
    print(f"   [ERROR] Exception: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test SOW format generation"""

import json
from pathlib import Path
from agents.sow_mail_agent import make_sow_mail_agent

def test_sow_format():
    """Test SOW format generation"""
    print("="*60)
    print("TEST: SOW Format Generation")
    print("="*60)
    
    # Load report data
    report_path = Path('opportunities/57cd76db400c4e7ca895d40bf6454173/report.json')
    if not report_path.exists():
        print(f"ERROR: Report not found: {report_path}")
        return False
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report_data = json.load(f)
    
    print(f"\n[INFO] Loaded report: {report_path}")
    print(f"[INFO] Event: {report_data.get('opportunity_info', {}).get('title', 'N/A')}")
    print(f"[INFO] Date Range: {report_data.get('event_requirements', {}).get('date_range', 'N/A')}")
    print(f"[INFO] Participants: {report_data.get('event_requirements', {}).get('participants_target', 'N/A')}")
    
    # Create agent
    print("\n[STEP] Creating SOW Agent...")
    agent = make_sow_mail_agent()
    print("[OK] Agent created")
    
    # Generate SOW
    print("\n[STEP] Generating SOW...")
    sow_result = agent.generate_sow(report_data)
    
    print("[OK] SOW generated successfully!")
    print(f"     - Text length: {len(sow_result['sow_text'])} chars")
    print(f"     - HTML length: {len(sow_result['sow_html'])} chars")
    
    # Save SOW to file
    output_path = Path('opportunities/57cd76db400c4e7ca895d40bf6454173/sow_formatted.md')
    output_path.write_text(sow_result['sow_text'], encoding='utf-8')
    print(f"\n[OK] SOW saved to: {output_path}")
    
    # Preview
    print("\n" + "="*60)
    print("SOW PREVIEW (first 2000 chars):")
    print("="*60)
    print(sow_result['sow_text'][:2000])
    print("\n... (truncated)")
    
    # Check for key sections
    sow_text = sow_result['sow_text']
    checks = {
        'APPENDIX A': 'APPENDIX A' in sow_text,
        'Meeting Information': 'Meeting Information' in sow_text,
        'Sleeping Room Requirements': 'Sleeping Room Requirements' in sow_text,
        'Function Space Requirements': 'Function Space Requirements' in sow_text,
        'Detailed Setup/Audio Visual': 'Detailed Setup/Audio Visual' in sow_text or 'Detailed Setup' in sow_text,
        'LIGHT REFRESHMENTS': 'LIGHT REFRESHMENTS' in sow_text or 'Light Refreshments' in sow_text,
        'Pre-con Meeting': 'Pre-con Meeting' in sow_text or 'Pre-conference' in sow_text,
    }
    
    print("\n" + "="*60)
    print("SECTION CHECKS:")
    print("="*60)
    for section, found in checks.items():
        status = "[OK]" if found else "[MISSING]"
        print(f"  {status} {section}")
    
    all_found = all(checks.values())
    if all_found:
        print("\n[SUCCESS] All required sections found!")
    else:
        print("\n[WARNING] Some sections missing")
    
    return all_found

if __name__ == "__main__":
    try:
        success = test_sow_format()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


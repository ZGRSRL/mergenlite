#!/usr/bin/env python3
"""Test Notice ID search for W50S7526QA010"""

import sys
import os
import logging
from datetime import datetime, timedelta

# .env dosyasını yükle
try:
    from dotenv import load_dotenv
    load_dotenv('mergen/.env')
    load_dotenv('.env')
except:
    pass

# Logging ayarla
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from sam_integration import SAMIntegration

def test_notice_search(notice_id: str):
    """Test Notice ID search"""
    print(f"\n{'='*60}")
    print(f"Testing Notice ID Search: {notice_id}")
    print(f"{'='*60}\n")
    
    sam = SAMIntegration()
    
    # API Key kontrolü
    if not sam.api_key:
        print("[ERROR] API Key not found!")
        print("Please check your .env file in mergen/.env or .env")
        return
    
    print(f"[OK] API Key loaded: {sam.api_key[:20]}...")
    print(f"[OK] API Key length: {len(sam.api_key)}")
    
    # Test 1: search_by_any_id
    print(f"\n[TEST 1] Using search_by_any_id...")
    try:
        results = sam.search_by_any_id(notice_id)
        print(f"[RESULT] Found {len(results)} results")
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n  Result {i}:")
                print(f"    Notice ID: {result.get('noticeId', 'N/A')}")
                print(f"    Opportunity ID: {result.get('opportunityId', 'N/A')}")
                print(f"    Title: {result.get('title', 'N/A')[:80]}")
                print(f"    Posted Date: {result.get('postedDate', 'N/A')}")
        else:
            print("[WARNING] No results found")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    # Test 2: fetch_by_notice_id
    print(f"\n[TEST 2] Using fetch_by_notice_id...")
    try:
        results = sam.fetch_by_notice_id(notice_id)
        print(f"[RESULT] Found {len(results)} results")
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n  Result {i}:")
                print(f"    Notice ID: {result.get('noticeId', 'N/A')}")
                print(f"    Opportunity ID: {result.get('opportunityId', 'N/A')}")
                print(f"    Title: {result.get('title', 'N/A')[:80]}")
                print(f"    Posted Date: {result.get('postedDate', 'N/A')}")
        else:
            print("[WARNING] No results found")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    # Test 3: Genel arama (keyword ile)
    print(f"\n[TEST 3] Using general search with keyword...")
    try:
        results = sam.fetch_opportunities(keywords=notice_id, days_back=365, limit=50)
        print(f"[RESULT] Found {len(results)} results")
        if results:
            # Notice ID ile eşleşenleri bul
            matching = [r for r in results if notice_id.lower() in str(r.get('noticeId', '')).lower()]
            print(f"[MATCH] {len(matching)} results match Notice ID")
            for i, result in enumerate(matching[:3], 1):
                print(f"\n  Match {i}:")
                print(f"    Notice ID: {result.get('noticeId', 'N/A')}")
                print(f"    Title: {result.get('title', 'N/A')[:80]}")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Description API
    print(f"\n[TEST 4] Using get_opportunity_details...")
    try:
        details = sam.get_opportunity_details(notice_id)
        if details.get('success'):
            print("[SUCCESS] Found via description API")
            data = details.get('data', {})
            print(f"    Title: {data.get('title', 'N/A')[:80]}")
            print(f"    Opportunity ID: {data.get('opportunityId', 'N/A')}")
        else:
            print(f"[FAILED] {details.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("Test completed!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    notice_id = sys.argv[1] if len(sys.argv) > 1 else "W50S7526QA010"
    test_notice_search(notice_id)




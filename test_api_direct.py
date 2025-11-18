#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Direkt API testi - Notice ID ve NAICS"""

import os
import sys
from dotenv import load_dotenv

load_dotenv('mergen/.env', override=True)

from sam_integration import SAMIntegration
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

print("="*60)
print("API Test - Notice ID ve NAICS")
print("="*60)

sam = SAMIntegration()
print(f"\nAPI Key: {'Var' if sam.api_key else 'Yok'}")

# Test 1: Notice ID
print("\n" + "-"*60)
print("Test 1: Notice ID W50S7526QA010")
print("-"*60)
try:
    result = sam.search_by_any_id("W50S7526QA010")
    print(f"Sonuc: {len(result)} firsat")
    if result:
        print(f"Notice ID: {result[0].get('noticeId', 'N/A')}")
        print(f"Title: {result[0].get('title', 'N/A')[:60]}...")
except Exception as e:
    print(f"Hata: {e}")

# Test 2: NAICS 721110
print("\n" + "-"*60)
print("Test 2: NAICS 721110 (Son 60 gun, Limit 10)")
print("-"*60)
try:
    result = sam.fetch_opportunities(
        naics_codes=['721110'],
        days_back=60,
        limit=10
    )
    print(f"Sonuc: {len(result)} firsat")
    if result:
        for i, opp in enumerate(result[:3], 1):
            print(f"\n{i}. {opp.get('noticeId', 'N/A')} / {opp.get('opportunityId', 'N/A')}")
            print(f"   Title: {opp.get('title', 'N/A')[:60]}...")
            print(f"   NAICS: {opp.get('naicsCode', 'N/A')}")
            print(f"   Date: {opp.get('postedDate', 'N/A')}")
    else:
        print("Sonuc yok - API loglarini kontrol edin")
except Exception as e:
    print(f"Hata: {e}")
    import traceback
    traceback.print_exc()

# Test 3: NAICS 721110 - Daha genis tarih
print("\n" + "-"*60)
print("Test 3: NAICS 721110 (Son 180 gun, Limit 10)")
print("-"*60)
try:
    result = sam.fetch_opportunities(
        naics_codes=['721110'],
        days_back=180,
        limit=10
    )
    print(f"Sonuc: {len(result)} firsat")
    if result:
        for i, opp in enumerate(result[:3], 1):
            print(f"\n{i}. {opp.get('noticeId', 'N/A')} / {opp.get('opportunityId', 'N/A')}")
            print(f"   Title: {opp.get('title', 'N/A')[:60]}...")
except Exception as e:
    print(f"Hata: {e}")

print("\n" + "="*60)
print("Test tamamlandi!")
print("="*60)


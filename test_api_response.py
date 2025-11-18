#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API response'u kontrol et - opportunityId neden gelmiyor?"""
import os
import sys
from dotenv import load_dotenv
from sam_integration import SAMIntegration
import json

# Windows encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# .env yükle
env_paths = ['mergen/.env', '.env']
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        break
else:
    load_dotenv(override=True)

print("=" * 60)
print("API Response Kontrolu")
print("=" * 60)

sam = SAMIntegration()
opportunities = sam.fetch_opportunities(
    naics_codes=['721110'],
    days_back=60,
    limit=5
)

print(f"\nToplam {len(opportunities)} fırsat bulundu\n")

if opportunities:
    print("Ilk 3 kaydin detaylari:")
    print("-" * 60)
    
    for i, opp in enumerate(opportunities[:3], 1):
        print(f"\n{i}. Kayit:")
        print(f"   Keys: {list(opp.keys())}")
        print(f"   opportunityId: {opp.get('opportunityId', 'YOK')}")
        print(f"   noticeId: {opp.get('noticeId', 'YOK')}")
        print(f"   title: {opp.get('title', 'N/A')[:50]}...")
        
        # raw_data kontrolü
        raw_data = opp.get('raw_data', {})
        if raw_data:
            print(f"   raw_data keys: {list(raw_data.keys())[:10]}")
            print(f"   raw_data.opportunityId: {raw_data.get('opportunityId', 'YOK')}")
            print(f"   raw_data.noticeId: {raw_data.get('noticeId', 'YOK')}")
        
        print()
else:
    print("❌ API'den veri gelmedi!")

print("=" * 60)


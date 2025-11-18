#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test 721110 araması"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from sam_integration import SAMIntegration
import logging

logging.basicConfig(level=logging.INFO)

print("=" * 60)
print("721110 Arama Testi")
print("=" * 60)

try:
    sam = SAMIntegration()
    print(f"\n1. API Key: {'VAR' if sam.api_key else 'YOK'}")
    print(f"2. API Version: {sam.get_api_version()}")
    
    if not sam.api_key:
        print("\n❌ API Key yok! Arama yapılamaz.")
        sys.exit(1)
    
    print("\n3. 721110 ile arama yapılıyor...")
    opps = sam.fetch_opportunities(
        naics_codes=['721110'],
        days_back=30,
        limit=10
    )
    
    print(f"\n4. Sonuç: {len(opps)} kayıt bulundu")
    
    if opps:
        print("\n5. İlk 3 kayıt:")
        for i, opp in enumerate(opps[:3], 1):
            opp_id = opp.get('opportunityId') or opp.get('noticeId', 'N/A')
            title = opp.get('title', 'Başlık Yok')[:60]
            print(f"   {i}. {opp_id}: {title}...")
    else:
        print("\n⚠️ Sonuç bulunamadı!")
        print("   Olası nedenler:")
        print("   - API quota limit aşıldı")
        print("   - Son 30 günde 721110 için ilan yok")
        print("   - API hatası")
    
    print("\n" + "=" * 60)

except Exception as e:
    print(f"\n❌ Hata: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


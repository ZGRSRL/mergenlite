#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""API test script - Notice ID ve NAICS araması"""

import os
import sys
from dotenv import load_dotenv

# Encoding ayarla
import sys
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# .env yükle
load_dotenv('mergen/.env', override=True)

from sam_integration import SAMIntegration

def test_notice_id(notice_id: str):
    """Notice ID ile arama testi"""
    print(f"\n{'='*60}")
    print(f"Notice ID Testi: {notice_id}")
    print(f"{'='*60}")
    
    sam = SAMIntegration()
    print(f"API Key durumu: {'Var' if sam.api_key else 'Yok'}")
    
    if not sam.api_key:
        print("⚠️ API Key bulunamadı! mergen/.env dosyasını kontrol edin.")
        return
    
    try:
        result = sam.search_by_any_id(notice_id)
        print(f"\n📊 Sonuç: {len(result)} fırsat bulundu")
        
        if result:
            opp = result[0]
            print(f"\n✅ İlk Sonuç:")
            print(f"  - Notice ID: {opp.get('noticeId', 'N/A')}")
            print(f"  - Opportunity ID: {opp.get('opportunityId', 'N/A')}")
            print(f"  - Başlık: {opp.get('title', 'N/A')[:80]}...")
            print(f"  - NAICS: {opp.get('naicsCode', 'N/A')}")
            print(f"  - Tarih: {opp.get('postedDate', 'N/A')}")
            print(f"  - Deadline: {opp.get('responseDeadLine', 'N/A')}")
        else:
            print("\n⚠️ Sonuç bulunamadı!")
            
    except Exception as e:
        print(f"\n❌ Hata: {str(e)}")
        import traceback
        traceback.print_exc()

def test_naics(naics_code: str, days_back: int = 60, limit: int = 10):
    """NAICS kodu ile arama testi"""
    print(f"\n{'='*60}")
    print(f"NAICS Testi: {naics_code} (Son {days_back} gun, Limit: {limit})")
    print(f"{'='*60}")
    
    sam = SAMIntegration()
    print(f"API Key durumu: {'Var' if sam.api_key else 'Yok'}")
    
    if not sam.api_key:
        print("⚠️ API Key bulunamadı! mergen/.env dosyasını kontrol edin.")
        return
    
    try:
        result = sam.fetch_opportunities(
            naics_codes=[naics_code],
            days_back=days_back,
            limit=limit
        )
        print(f"\nSonuc: {len(result)} firsat bulundu")
        
        if result:
            print(f"\nIlk {min(5, len(result))} Firsat:")
            for i, opp in enumerate(result[:5], 1):
                print(f"\n  {i}. {opp.get('noticeId', 'N/A')} / {opp.get('opportunityId', 'N/A')}")
                title = opp.get('title', 'N/A')
                if isinstance(title, str):
                    print(f"     Baslik: {title[:70]}...")
                else:
                    print(f"     Baslik: {title}")
                print(f"     NAICS: {opp.get('naicsCode', 'N/A')}")
                print(f"     Tarih: {opp.get('postedDate', 'N/A')}")
        else:
            print("\nSonuc bulunamadi!")
            print("Oneriler:")
            print("  - Tarih aralığını genişletin (örn: 90 veya 180 gün)")
            print("  - Terminal loglarını kontrol edin")
            
    except Exception as e:
        print(f"\n❌ Hata: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Notice ID testi
    test_notice_id("W50S7526QA010")
    
    # NAICS testi
    test_naics("721110", days_back=60, limit=10)
    
    print(f"\n{'='*60}")
    print("Test tamamlandi!")
    print(f"{'='*60}")


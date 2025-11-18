#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database'den Opportunity Kontrolü
raw_data.resourceLinks ve raw_data.attachments alanlarını kontrol eder
"""

import os
import sys
import json
from datetime import datetime

def check_opportunity_from_db(opportunity_id: str = None, limit: int = 5):
    """Database'den opportunity'leri kontrol et"""
    print("=" * 60)
    print("Database Opportunity Kontrolü")
    print("=" * 60)
    
    try:
        from backend_utils import load_opportunities_from_db, get_db_session, DB_AVAILABLE
        from mergenlite_models import Opportunity
        
        if not DB_AVAILABLE:
            print("❌ [ERROR] Database bağlantısı yok (DB_AVAILABLE = False)")
            return False
        
        # Database'den yükle
        opportunities = load_opportunities_from_db(limit=limit)
        
        if not opportunities:
            print("⚠️ [WARN] Database'de opportunity bulunamadı")
            return False
        
        print(f"✅ [OK] {len(opportunities)} opportunity yüklendi\n")
        
        # Her opportunity için raw_data kontrolü
        found_resource_links = False
        for idx, opp in enumerate(opportunities, 1):
            opp_id = opp.get('opportunityId') or opp.get('opportunity_id', 'N/A')
            title = opp.get('title', 'Başlık Yok')[:50]
            
            print(f"[{idx}] Opportunity ID: {opp_id}")
            print(f"    Title: {title}...")
            
            raw_data = opp.get('raw_data', {})
            if not raw_data:
                print("    ⚠️ raw_data boş")
                continue
            
            if isinstance(raw_data, str):
                try:
                    raw_data = json.loads(raw_data)
                except:
                    print("    ❌ raw_data JSON parse edilemedi")
                    continue
            
            # resourceLinks kontrolü
            resource_links = raw_data.get('resourceLinks', [])
            if resource_links:
                print(f"    ✅ Found resourceLinks: {len(resource_links)} adet")
                found_resource_links = True
                # İlk birkaç link'i göster
                for i, link in enumerate(resource_links[:3], 1):
                    url = link.get('url', link.get('link', 'N/A')) if isinstance(link, dict) else str(link)
                    print(f"       [{i}] {url[:60]}...")
            else:
                print("    ⚠️ resourceLinks bulunamadı")
            
            # attachments kontrolü
            attachments = raw_data.get('attachments', [])
            if attachments:
                print(f"    ✅ Found attachments: {len(attachments)} adet")
                found_resource_links = True
                # İlk birkaç attachment'ı göster
                for i, att in enumerate(attachments[:3], 1):
                    if isinstance(att, dict):
                        name = att.get('name', att.get('filename', 'N/A'))
                        url = att.get('url', att.get('link', 'N/A'))
                        print(f"       [{i}] {name} → {url[:50]}...")
                    else:
                        print(f"       [{i}] {str(att)[:60]}...")
            else:
                print("    ⚠️ attachments bulunamadı")
            
            print()
        
        print("=" * 60)
        
        if found_resource_links:
            print("✅ [SUCCESS] resourceLinks/attachments bulundu!")
            return True
        else:
            print("⚠️ [WARN] resourceLinks/attachments bulunamadı")
            return False
            
    except ImportError as e:
        print(f"❌ [ERROR] Import hatası: {e}")
        return False
    except Exception as e:
        print(f"❌ [ERROR] Kontrol hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Komut satırı argümanı varsa kullan
    opp_id = sys.argv[1] if len(sys.argv) > 1 else None
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    success = check_opportunity_from_db(opportunity_id=opp_id, limit=limit)
    sys.exit(0 if success else 1)

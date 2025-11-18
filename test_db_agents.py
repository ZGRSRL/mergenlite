#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database'den kayıt çekip AI ajanları ile analiz testi"""

import sys
import os
import io

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

from backend_utils import get_db_session, load_opportunities_from_db, DB_AVAILABLE
from mergenlite_models import Opportunity
from datetime import datetime

print("=" * 60)
print("Database'den Kayit Cekme ve AI Ajanlari Testi")
print("=" * 60)

if not DB_AVAILABLE:
    print("[ERROR] Database baglantisi yok!")
    sys.exit(1)

try:
    # Database'den son 5 kayıt çek
    print("\n[1] Database'den kayitlar cekiliyor...")
    opportunities = load_opportunities_from_db(limit=5)
    
    if not opportunities:
        print("[WARN] Database'de kayit bulunamadi!")
        sys.exit(0)
    
    print(f"[OK] {len(opportunities)} kayit bulundu\n")
    
    # İlk kaydı göster
    first_opp = opportunities[0]
    opp_id = first_opp.get('opportunityId') or first_opp.get('noticeId', 'N/A')
    title = first_opp.get('title', 'Baslik Yok')
    
    print("=" * 60)
    print("SECILEN KAYIT:")
    print("=" * 60)
    print(f"Opportunity ID: {opp_id}")
    print(f"Notice ID: {first_opp.get('noticeId', 'N/A')}")
    print(f"Baslik: {title}")
    print(f"NAICS: {first_opp.get('naicsCode', 'N/A')}")
    
    # raw_data kontrolü
    raw_data = first_opp.get('raw_data')
    if raw_data:
        if isinstance(raw_data, dict):
            resource_links = raw_data.get('resourceLinks', [])
            attachments = raw_data.get('attachments', [])
            print(f"resourceLinks: {len(resource_links)} adet")
            print(f"attachments: {len(attachments)} adet")
    
    print("\n" + "=" * 60)
    print("[2] AI Ajanlari ile analiz baslatiliyor...")
    print("=" * 60)
    
    # analyze_opportunity fonksiyonunu import et
    try:
        from opportunity_runner import analyze_opportunity
        from backend_utils import sanitize_code
        
        # Opportunity code oluştur
        notice_id = first_opp.get('noticeId') or ''
        opportunity_id = first_opp.get('opportunityId') or ''
        
        code = sanitize_code(notice_id or opportunity_id or 'test')
        
        print(f"\n[INFO] Analiz parametreleri:")
        print(f"  - Opportunity Code: {code}")
        print(f"  - Notice ID: {notice_id}")
        print(f"  - Opportunity ID: {opportunity_id}")
        print(f"  - Download from SAM.gov: True")
        
        print(f"\n[INFO] Analiz baslatiliyor...")
        print(f"      (Bu islem biraz zaman alabilir)")
        
        # Analiz başlat
        result = analyze_opportunity(
            base_dir='.',
            opportunity_code=code,
            notice_id=notice_id,
            opportunity_id=opportunity_id,
            download_from_sam_gov=True
        )
        
        if result:
            print(f"\n[OK] Analiz tamamlandi!")
            print(f"      Sonuc: {type(result)}")
            
            # Sonuç detayları
            if isinstance(result, dict):
                print(f"\n[INFO] Analiz sonucu detaylari:")
                for key, value in result.items():
                    if isinstance(value, (str, int, float, bool)):
                        print(f"  - {key}: {value}")
                    elif isinstance(value, dict):
                        print(f"  - {key}: (dict, {len(value)} keys)")
                    elif isinstance(value, list):
                        print(f"  - {key}: (list, {len(value)} items)")
                    else:
                        print(f"  - {key}: {type(value).__name__}")
        else:
            print(f"\n[WARN] Analiz sonucu alinamadi (None donduruldu)")
            
    except ImportError as e:
        print(f"[ERROR] analyze_opportunity import hatasi: {e}")
        print(f"        opportunity_runner.py dosyasini kontrol edin")
    except Exception as e:
        print(f"\n[ERROR] Analiz hatasi: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("[OK] Test tamamlandi!")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] Genel hata: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


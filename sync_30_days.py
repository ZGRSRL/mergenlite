#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SAM.gov'dan 1 aylık (30 gün) tüm kayıtları çek ve database'e kaydet"""

import sys
import os
import io
from datetime import datetime

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

from backend_utils import sync_opportunities_from_sam, DB_AVAILABLE, get_db_session
from mergenlite_models import Opportunity
from sam_integration import SAMIntegration

print("=" * 60)
print("SAM.gov 1 Yillik (365 Gun) Kayit Cekme")
print("=" * 60)

if not DB_AVAILABLE:
    print("[ERROR] Database baglantisi yok!")
    sys.exit(1)

try:
    # Önce mevcut kayıt sayısını kontrol et
    db = get_db_session()
    if db:
        total_before = db.query(Opportunity).count()
        db.close()
        print(f"\n[INFO] Mevcut database kayit sayisi: {total_before}")
    else:
        print("[WARN] Database session olusturulamadi, devam ediliyor...")
        total_before = 0
    
    print("\n[1] SAM.gov API'den kayitlar cekiliyor...")
    print("    - Tarih araligi: Son 365 gun (1 yil) - 3 aylik parcalar halinde")
    print("    - NAICS: 721110 (Hotel/Motel)")
    print("    - Limit: 1000 kayit per parca")
    print("    - Bu islem biraz zaman alabilir...\n")
    
    # API 1 yıllık aralığı desteklemiyor, 3 aylık (90 gün) parçalara böl
    # 1 yıl = 4 parça (her biri 90 gün)
    total_new = 0
    total_updated = 0
    
    for quarter in range(4):
        days_start = quarter * 90
        days_end = min((quarter + 1) * 90, 365)
        days_back = days_end - days_start
        
        print(f"\n[Parca {quarter + 1}/4] Son {days_end} gunden {days_start} gune kadar...")
        
        # Her parça için sync yap
        sync_opportunities_from_sam(
            naics_code="721110",
            days_back=days_end,  # Son X günü çek
            limit=1000,
            show_progress=False
        )
        
        # Kısa bir bekleme (rate limiting için)
        import time
        if quarter < 3:  # Son parça değilse bekle
            time.sleep(2)
    
    print("\n[OK] Tum parcalar tamamlandi!")
    
    print("\n[2] Database kontrol ediliyor...")
    
    # Yeni kayıt sayısını kontrol et
    db = get_db_session()
    if db:
        total_after = db.query(Opportunity).count()
        new_count = total_after - total_before
        
        # Son 30 dakikada eklenen kayıtları say
        from datetime import timedelta
        thirty_min_ago = datetime.now() - timedelta(minutes=30)
        recent = db.query(Opportunity).filter(Opportunity.created_at >= thirty_min_ago).count()
        
        db.close()
        
        print(f"\n[OK] Senkronizasyon tamamlandi!")
        print(f"    - Onceki kayit sayisi: {total_before}")
        print(f"    - Yeni kayit sayisi: {total_after}")
        print(f"    - Eklenen/Guncellenen: {new_count}")
        print(f"    - Son 30 dakikada eklenen: {recent}")
        
        # Son 5 kayıt göster
        print(f"\n[INFO] Son 5 kayit:")
        db = get_db_session()
        if db:
            recent_opps = db.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(5).all()
            for i, opp in enumerate(recent_opps, 1):
                opp_id = opp.opportunity_id or 'N/A'
                title = (opp.title or 'Baslik Yok')[:50]
                created = opp.created_at.strftime('%Y-%m-%d %H:%M') if opp.created_at else 'N/A'
                
                # raw_data kontrolü
                has_resource_links = False
                if opp.raw_data and isinstance(opp.raw_data, dict):
                    has_resource_links = bool(opp.raw_data.get('resourceLinks') or opp.raw_data.get('attachments'))
                
                print(f"   {i}. {opp_id[:20]}...")
                print(f"      Baslik: {title}...")
                print(f"      Olusturulma: {created}")
                print(f"      resourceLinks: {'VAR' if has_resource_links else 'YOK'}")
            db.close()
    else:
        print("[WARN] Database kontrol edilemedi")
    
    print("\n" + "=" * 60)
    print("[OK] Islem tamamlandi!")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] Hata: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


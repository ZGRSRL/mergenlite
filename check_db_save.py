#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database'e kayıt kontrolü"""

import sys
import os
import io

# Windows console encoding fix
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(__file__))

from backend_utils import get_db_session, DB_AVAILABLE
from mergenlite_models import Opportunity
from datetime import datetime, timedelta

print("=" * 60)
print("Database Kayıt Kontrolü")
print("=" * 60)

if not DB_AVAILABLE:
    print("[ERROR] Database baglantisi yok!")
    sys.exit(1)

try:
    db = get_db_session()
    if not db:
        print("[ERROR] Database session olusturulamadi!")
        sys.exit(1)
    
    # Toplam kayıt sayısı
    total = db.query(Opportunity).count()
    print(f"\n[OK] Toplam kayit: {total}")
    
    # Son 24 saatte eklenenler
    yesterday = datetime.now() - timedelta(days=1)
    recent = db.query(Opportunity).filter(Opportunity.created_at >= yesterday).count()
    print(f"[OK] Son 24 saatte eklenen: {recent}")
    
    # Son 5 kayıt
    print(f"\nSon 5 kayit:")
    recent_opps = db.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(5).all()
    
    for i, opp in enumerate(recent_opps, 1):
        opp_id = opp.opportunity_id or 'N/A'
        title = (opp.title or 'Başlık Yok')[:50]
        created = opp.created_at.strftime('%Y-%m-%d %H:%M') if opp.created_at else 'N/A'
        
        # raw_data kontrolü
        has_raw_data = bool(opp.raw_data)
        has_resource_links = False
        if has_raw_data and isinstance(opp.raw_data, dict):
            has_resource_links = bool(opp.raw_data.get('resourceLinks') or opp.raw_data.get('attachments'))
        
        print(f"   {i}. {opp_id[:20]}...")
        print(f"      Başlık: {title}...")
        print(f"      Oluşturulma: {created}")
        print(f"      raw_data: {'VAR' if has_raw_data else 'YOK'}")
        print(f"      resourceLinks: {'VAR' if has_resource_links else 'YOK'}")
        print()
    
    db.close()
    print("=" * 60)
    print("[OK] Kontrol tamamlandi!")

except Exception as e:
    print(f"\n[ERROR] Hata: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


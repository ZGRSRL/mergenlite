#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database kontrol scripti"""

import os
import sys
from dotenv import load_dotenv

# .env yükle
load_dotenv('mergen/.env', override=True)

try:
    from app import get_db_session, Opportunity, DB_AVAILABLE
    from datetime import datetime
    
    print("="*60)
    print("Database Kontrol")
    print("="*60)
    
    if not DB_AVAILABLE:
        print("UYARI: Database baglantisi yok!")
        sys.exit(1)
    
    db = get_db_session()
    if not db:
        print("HATA: Database session olusturulamadi!")
        sys.exit(1)
    
    # Toplam kayıt sayısı
    total_count = db.query(Opportunity).count()
    print(f"\nToplam firsat sayisi: {total_count}")
    
    # Son 10 kayıt
    recent = db.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(10).all()
    print(f"\nSon 10 kayit:")
    for i, r in enumerate(recent, 1):
        print(f"  {i}. {r.opportunity_id or 'N/A'}: {r.title[:60] if r.title else 'N/A'}...")
        print(f"     NAICS: {r.naics_code or 'N/A'}, Olusturulma: {r.created_at}")
    
    # NAICS 721110 kayıtları
    naics_count = db.query(Opportunity).filter(Opportunity.naics_code == '721110').count()
    print(f"\nNAICS 721110 kayit sayisi: {naics_count}")
    
    # Bugün eklenenler
    today = datetime.now().date()
    today_count = db.query(Opportunity).filter(
        Opportunity.created_at >= datetime.combine(today, datetime.min.time())
    ).count()
    print(f"Bugun eklenen kayit sayisi: {today_count}")
    
    db.close()
    print("\n" + "="*60)
    print("Kontrol tamamlandi!")
    print("="*60)
    
except Exception as e:
    print(f"HATA: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


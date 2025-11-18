#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mevcut kayıtların SAM.gov linklerini güncelle"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from mergenlite_models import Opportunity

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

# Veritabanı bağlantısı
db_host = os.getenv('DB_HOST', 'localhost')
if db_host == 'db':
    db_host = 'localhost'

DATABASE_URL = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@{db_host}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'mergenlite')}"

print("=" * 60)
print("SAM.gov Link Guncelleme")
print("=" * 60)

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Tüm kayıtları al
    opportunities = db.query(Opportunity).all()
    print(f"\nToplam {len(opportunities)} kayit bulundu")
    
    updated_count = 0
    for opp in opportunities:
        try:
            opportunity_id = opp.opportunity_id or ''
            notice_id = getattr(opp, 'notice_id', None) or ''
            
            # Mevcut link var mı kontrol et
            if opp.sam_gov_link:
                continue  # Zaten var, atla
            
            # Yeni link oluştur
            sam_gov_link = None
            if opportunity_id and len(opportunity_id) == 32:  # Opportunity ID (32 karakter hex)
                sam_gov_link = f"https://sam.gov/opp/{opportunity_id}/view"
            elif notice_id:
                sam_gov_link = f"https://sam.gov/opportunities/search?noticeId={notice_id}"
            
            if sam_gov_link:
                opp.sam_gov_link = sam_gov_link
                updated_count += 1
        except Exception as e:
            print(f"  ⚠️ Hata (opportunity_id: {getattr(opp, 'opportunity_id', 'N/A')}): {e}")
            continue
    
    if updated_count > 0:
        db.commit()
        print(f"\n✅ {updated_count} kayit guncellendi")
    else:
        print(f"\nℹ️ Guncellenecek kayit yok (tum linkler mevcut)")
    
    db.close()
    
except Exception as e:
    print(f"\n❌ Hata: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)


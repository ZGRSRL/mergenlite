#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database'deki kayıtları kontrol et"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
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
print("Database Kayit Kontrolu")
print("=" * 60)

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Toplam kayıt sayısı
    total = db.query(Opportunity).count()
    print(f"\nToplam kayit: {total}")
    
    if total == 0:
        print("\n❌ Database'de kayit yok!")
        print("   Neden: Muhtemelen opportunityId olmadigi icin kayitlar skip edildi")
    else:
        # Son 10 kaydı göster
        print(f"\nSon 10 kayit:")
        print("-" * 60)
        
        opportunities = db.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(10).all()
        
        for i, opp in enumerate(opportunities, 1):
            notice_id = getattr(opp, 'notice_id', None) or 'YOK'
            raw_data = opp.raw_data or {}
            raw_notice_id = raw_data.get('noticeId', 'YOK')
            raw_opp_id = raw_data.get('opportunityId', 'YOK')
            
            print(f"\n{i}. {opp.title[:50]}...")
            print(f"   opportunity_id: {opp.opportunity_id[:30] if opp.opportunity_id else 'YOK'}...")
            print(f"   notice_id (model): {notice_id[:30] if notice_id != 'YOK' else 'YOK'}...")
            print(f"   raw_data.noticeId: {raw_notice_id[:30] if raw_notice_id != 'YOK' else 'YOK'}...")
            print(f"   raw_data.opportunityId: {raw_opp_id[:30] if raw_opp_id != 'YOK' else 'YOK'}...")
            print(f"   created_at: {opp.created_at}")
        
        # notice_id olmayan kayıtlar
        print(f"\n\nNotice ID durumu:")
        print("-" * 60)
        with_notice_id = db.query(Opportunity).filter(Opportunity.notice_id.isnot(None)).count()
        without_notice_id = total - with_notice_id
        print(f"   notice_id olan: {with_notice_id}")
        print(f"   notice_id olmayan: {without_notice_id}")
    
    db.close()
    
except Exception as e:
    print(f"\n❌ Hata: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)


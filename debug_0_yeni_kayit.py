#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0 yeni kayıt sorununu debug et"""
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mergenlite_models import Opportunity
from sam_integration import SAMIntegration

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

def debug_opportunity_save():
    """Neden 0 yeni kayıt ekleniyor debug et"""
    
    print("=" * 60)
    print("DEBUG: 0 Yeni Kayit Sorunu")
    print("=" * 60)
    
    # 1. API'den veri çek
    print("\n1. API'den veri cekiliyor...")
    sam = SAMIntegration()
    opportunities = sam.fetch_opportunities(
        naics_codes=['721110'],
        days_back=60,
        limit=10
    )
    
    print(f"   API'den {len(opportunities)} fırsat geldi")
    
    if not opportunities:
        print("   ❌ API'den veri gelmedi!")
        return
    
    # 2. İlk 3 kaydı incele
    print("\n2. Ilk 3 kayit inceleniyor...")
    for i, opp in enumerate(opportunities[:3], 1):
        opp_id = opp.get('opportunityId', '')
        notice_id = opp.get('noticeId', '')
        title = opp.get('title', 'N/A')[:50]
        
        print(f"\n   Kayit {i}:")
        print(f"      Opportunity ID: {opp_id[:30] if opp_id else 'YOK'}...")
        print(f"      Notice ID: {notice_id[:30] if notice_id else 'YOK'}...")
        print(f"      Baslik: {title}...")
        
        if not opp_id:
            print(f"      ⚠️ SORUN: Opportunity ID yok! Bu kayit skip edilecek.")
    
    # 3. Veritabanı durumu
    print("\n3. Veritabani durumu kontrol ediliyor...")
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        total_count = db.query(Opportunity).count()
        print(f"   Toplam kayit: {total_count}")
        
        # İlk 3 opportunity_id'yi kontrol et
        print("\n4. Ilk 3 kaydin veritabaninda olup olmadigi kontrol ediliyor...")
        count_existing = 0
        count_new = 0
        
        for opp in opportunities[:3]:
            opp_id = opp.get('opportunityId', '').strip()
            notice_id = opp.get('noticeId', '').strip()
            
            if not opp_id:
                print(f"   ⚠️ Opportunity ID yok, skip ediliyor")
                continue
            
            existing = db.query(Opportunity).filter(
                Opportunity.opportunity_id == opp_id
            ).first()
            
            if existing:
                print(f"   ✅ Mevcut: {opp_id[:20]}... (notice_id: {existing.notice_id})")
                count_existing += 1
            else:
                print(f"   🆕 Yeni: {opp_id[:20]}... (notice_id: {notice_id[:20] if notice_id else 'YOK'})")
                count_new += 1
        
        print(f"\n   Sonuc: {count_existing} mevcut, {count_new} yeni")
        
        # 5. Veritabanı şeması kontrolü
        print("\n5. Veritabani semasi kontrol ediliyor...")
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('opportunities')]
        
        has_notice_id = 'notice_id' in columns
        has_solicitation_number = 'solicitation_number' in columns
        
        print(f"   notice_id alani: {'✅ Var' if has_notice_id else '❌ YOK (migration gerekli!)'}")
        print(f"   solicitation_number alani: {'✅ Var' if has_solicitation_number else '❌ YOK (migration gerekli!)'}")
        
        if not has_notice_id:
            print("\n   ⚠️ UYARI: notice_id alani yok! Migration calistirilmali:")
            print("      python add_notice_id_migration.py")
        
        db.close()
        
    except Exception as e:
        print(f"   ❌ Veritabani hatasi: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("DEBUG Tamamlandi")
    print("=" * 60)

if __name__ == "__main__":
    debug_opportunity_save()


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""load_opportunities_from_db fonksiyonunu test et"""
import os
import sys
from dotenv import load_dotenv

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

# app.py'deki fonksiyonu test et
import sys
sys.path.insert(0, os.path.dirname(__file__))

print("=" * 60)
print("load_opportunities_from_db Test")
print("=" * 60)

try:
    # app.py'den import et
    from app import load_opportunities_from_db, get_db_session, DB_AVAILABLE
    from mergenlite_models import Opportunity
    
    print(f"\nDB_AVAILABLE: {DB_AVAILABLE}")
    
    if not DB_AVAILABLE:
        print("❌ DB_AVAILABLE = False")
    else:
        # Direkt database sorgusu
        print("\n1. Direkt database sorgusu:")
        db = get_db_session()
        if db:
            count = db.query(Opportunity).count()
            print(f"   ✅ Database'de {count} kayıt var")
            
            # İlk 5 kaydı göster
            opps = db.query(Opportunity).order_by(Opportunity.created_at.desc()).limit(5).all()
            print(f"   İlk 5 kayıt:")
            for i, opp in enumerate(opps, 1):
                print(f"      {i}. {opp.title[:50]}... (ID: {opp.opportunity_id[:20] if opp.opportunity_id else 'N/A'}...)")
            
            db.close()
        else:
            print("   ❌ get_db_session() None döndü")
        
        # load_opportunities_from_db fonksiyonu
        print("\n2. load_opportunities_from_db() fonksiyonu:")
        result = load_opportunities_from_db(limit=10)
        print(f"   Sonuç: {len(result)} kayıt döndü")
        
        if result:
            print(f"   İlk 3 kayıt:")
            for i, opp in enumerate(result[:3], 1):
                print(f"      {i}. {opp.get('title', 'N/A')[:50]}...")
                print(f"         opportunityId: {opp.get('opportunityId', 'N/A')[:20] if opp.get('opportunityId') else 'N/A'}...")
                print(f"         noticeId: {opp.get('noticeId', 'N/A')[:20] if opp.get('noticeId') else 'N/A'}...")
        else:
            print("   ❌ Boş liste döndü!")
            print("   💡 Olası nedenler:")
            print("      - Exception oluştu ve sessizce boş liste döndü")
            print("      - Parse hatası")
            print("      - Database bağlantı sorunu")
    
except Exception as e:
    print(f"\n❌ Hata: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)


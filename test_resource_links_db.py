#!/usr/bin/env python3
"""
Test script: GSA API resourceLinks'in DB'ye kaydedilip kaydedilmediğini kontrol et
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mergenlite_models import Opportunity
import json

# Database connection
try:
    db_host = os.getenv('DB_HOST', 'localhost')
    if db_host == 'db':
        db_host = 'localhost'
    
    DATABASE_URL = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'postgres')}@{db_host}:{os.getenv('DB_PORT', '5432')}/mergenlite"
    
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Son 5 kaydı kontrol et - sadece gerekli kolonları seç
    opportunities = db.query(
        Opportunity.opportunity_id,
        Opportunity.title,
        Opportunity.raw_data
    ).order_by(Opportunity.created_at.desc()).limit(5).all()
    
    print(f"{len(opportunities)} kayit bulundu\n")
    
    for opp in opportunities:
        opp_id = opp.opportunity_id or 'N/A'
        print(f"Kayit: {opp_id}")
        print(f"   Baslik: {opp.title[:60] if opp.title else 'N/A'}...")
        
        raw_data = opp.raw_data or {}
        
        # resourceLinks kontrolü
        resource_links = raw_data.get('resourceLinks', [])
        attachments = raw_data.get('attachments', [])
        
        print(f"   resourceLinks: {len(resource_links)} adet")
        print(f"   attachments: {len(attachments)} adet")
        
        if resource_links:
            print(f"   OK: resourceLinks mevcut!")
            for i, link in enumerate(resource_links[:3]):  # İlk 3'ü göster
                if isinstance(link, dict):
                    link_url = link.get('url', link.get('link', 'N/A'))
                else:
                    link_url = str(link)
                print(f"      {i+1}. {link_url[:60]}...")
        elif attachments:
            print(f"   OK: attachments mevcut!")
            for i, att in enumerate(attachments[:3]):
                if isinstance(att, dict):
                    att_url = att.get('url', att.get('link', 'N/A'))
                else:
                    att_url = str(att)
                print(f"      {i+1}. {att_url[:60]}...")
        else:
            print(f"   UYARI: resourceLinks veya attachments bulunamadi")
            # raw_data keys'lerini göster
            if raw_data:
                print(f"   raw_data keys: {list(raw_data.keys())[:10]}")
        
        print()
    
    db.close()
    print("Test tamamlandi!")
    
except Exception as e:
    print(f"Hata: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


#!/usr/bin/env python3
"""
Test: Otomatik doküman indirme ve analiz akışı
1. GSA API'den fırsat çek
2. DB'ye kaydet (resourceLinks ile)
3. Otomatik doküman indir
4. Analiz başlat
"""
import os
import sys
from pathlib import Path

# Test için basit bir senaryo
print("Test Senaryosu:")
print("1. GSA API'den fırsat çekilecek")
print("2. DB'ye kaydedilecek (resourceLinks ile)")
print("3. Otomatik doküman indirme test edilecek")
print("4. Analiz başlatma test edilecek")
print()

# GSA client test
try:
    from gsa_opportunities_client import GSAPublicAPIClient
    
    client = GSAPublicAPIClient(api_key=os.getenv('GSA_API_KEY'))
    
    print("GSA Client test ediliyor...")
    # Test araması
    opportunities = client.fetch_opportunities(
        naics_codes=['721110'],
        days_back=30,
        limit=5
    )
    
    if opportunities:
        print(f"OK: {len(opportunities)} fırsat bulundu")
        
        # İlk fırsatı kontrol et
        opp = opportunities[0]
        print(f"\nİlk fırsat:")
        print(f"  Opportunity ID: {opp.get('opportunityId', 'N/A')}")
        print(f"  Notice ID: {opp.get('noticeId', 'N/A')}")
        print(f"  Title: {opp.get('title', 'N/A')[:60]}...")
        
        # resourceLinks kontrolü
        resource_links = opp.get('resourceLinks', [])
        attachments = opp.get('attachments', [])
        raw_data = opp.get('raw_data', {})
        
        print(f"\n  resourceLinks: {len(resource_links)} adet")
        print(f"  attachments: {len(attachments)} adet")
        print(f"  raw_data mevcut: {bool(raw_data)}")
        
        if resource_links:
            print(f"  OK: resourceLinks mevcut!")
            for i, link in enumerate(resource_links[:3]):
                if isinstance(link, dict):
                    url = link.get('url', link.get('link', 'N/A'))
                else:
                    url = str(link)
                print(f"    {i+1}. {url[:60]}...")
        elif raw_data and raw_data.get('resourceLinks'):
            print(f"  OK: raw_data içinde resourceLinks mevcut!")
        else:
            print(f"  UYARI: resourceLinks bulunamadi")
        
        # DB'ye kaydet testi
        try:
            from app import get_db_session, sync_opportunities_from_sam
            from mergenlite_models import Opportunity
            
            print(f"\nDB'ye kaydetme testi...")
            # Sadece test için - gerçek kayıt yapmadan kontrol et
            db = get_db_session()
            if db:
                # Mevcut kayıtları kontrol et
                existing = db.query(Opportunity).filter(
                    Opportunity.opportunity_id == opp.get('opportunityId', '')
                ).first()
                
                if existing:
                    raw_data_db = existing.raw_data or {}
                    resource_links_db = raw_data_db.get('resourceLinks', [])
                    print(f"  Mevcut kayit bulundu")
                    print(f"  DB'deki resourceLinks: {len(resource_links_db)} adet")
                    if resource_links_db:
                        print(f"  OK: DB'de resourceLinks mevcut!")
                    else:
                        print(f"  UYARI: DB'de resourceLinks yok - senkronizasyon gerekli")
                else:
                    print(f"  Yeni kayit - senkronizasyon sonrasi resourceLinks kaydedilecek")
                
                db.close()
        except Exception as e:
            print(f"  DB test hatasi: {e}")
        
        # Otomatik indirme testi
        try:
            from opportunity_runner import download_from_sam
            
            print(f"\nOtomatik dokuman indirme testi...")
            notice_id = opp.get('noticeId') or opp.get('solicitationNumber', '')
            opportunity_id = opp.get('opportunityId', '')
            
            if notice_id or opportunity_id:
                test_folder = Path(".") / "test_downloads"
                test_folder.mkdir(exist_ok=True)
                
                downloaded = download_from_sam(
                    folder=test_folder,
                    notice_id=notice_id,
                    opportunity_id=opportunity_id
                )
                
                if downloaded:
                    print(f"  OK: {len(downloaded)} dokuman indirildi!")
                    for doc in downloaded[:3]:
                        print(f"    - {doc.get('name', 'N/A')}")
                else:
                    print(f"  UYARI: Dokuman indirilemedi (resourceLinks yok veya URL'ler gecersiz)")
            else:
                print(f"  UYARI: Notice ID veya Opportunity ID yok")
        except Exception as e:
            print(f"  Indirme test hatasi: {e}")
            import traceback
            traceback.print_exc()
        
    else:
        print("UYARI: Firsat bulunamadi")
        
except Exception as e:
    print(f"Hata: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nTest tamamlandi!")


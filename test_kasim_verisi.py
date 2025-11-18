#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kasım 2025 verilerini çekme testi"""
import os
import sys
from dotenv import load_dotenv
from datetime import datetime, timedelta
from sam_integration import SAMIntegration

# Windows console encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# .env yükle
env_paths = ['mergen/.env', '.env']
env_loaded = False
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path, override=True)
        env_loaded = True
        print(f"✅ .env yüklendi: {env_path}")
        break

if not env_loaded:
    load_dotenv(override=True)

api_key = os.getenv('SAM_API_KEY', '')

if not api_key:
    print("❌ SAM_API_KEY bulunamadı!")
    print("Lütfen .env dosyasında SAM_API_KEY tanımlayın.")
    sys.exit(1)

print(f"✅ API Key yüklendi ({len(api_key)} karakter)")
print("="*60)

# SAM Integration oluştur
sam = SAMIntegration()

# Test 1: Kasım ayı için tarih aralığı (Kasım 1 - Kasım 30, 2025)
print("\n📅 TEST 1: Kasım 2025 Verileri (Kasım 1-30, 2025)")
print("="*60)

# Kasım ayı için tarih hesapla
nov_start = datetime(2025, 11, 1)
nov_end = datetime(2025, 11, 30)
today = datetime.now()

# Eğer bugün Kasım içindeyse, bugüne kadar
if today.month == 11 and today.year == 2025:
    nov_end = today

# days_back hesapla
days_back = (nov_end - nov_start).days + 1
print(f"📅 Tarih Aralığı: {nov_start.strftime('%Y-%m-%d')} - {nov_end.strftime('%Y-%m-%d')}")
print(f"📅 Days Back: {days_back} gün")

try:
    opportunities = sam.fetch_opportunities(
        naics_codes=['721110'],
        days_back=days_back,
        limit=100
    )
    
    print(f"\n✅ Sonuç: {len(opportunities)} fırsat bulundu")
    
    if opportunities:
        print("\n📋 İlk 5 Fırsat:")
        for i, opp in enumerate(opportunities[:5], 1):
            notice_id = opp.get('noticeId', 'N/A')
            opp_id = opp.get('opportunityId', 'N/A')
            title = opp.get('title', 'N/A')[:60]
            posted_date = opp.get('postedDate', 'N/A')
            updated_date = opp.get('updatedDate', 'N/A')
            
            print(f"\n  {i}. Notice ID: {notice_id}")
            print(f"     Opportunity ID: {opp_id}")
            print(f"     Başlık: {title}...")
            print(f"     Yayın Tarihi: {posted_date}")
            print(f"     Güncelleme: {updated_date}")
    else:
        print("\n⚠️ Sonuç bulunamadı")
        print("\n💡 Öneriler:")
        print("   - Tarih aralığını genişletin (örn: Ekim-Kasım)")
        print("   - Farklı bir NAICS kodu deneyin")
        print("   - API key'inizi kontrol edin")
        
except Exception as e:
    print(f"\n❌ Hata: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Son 60 gün (Kasım'ı kapsayacak şekilde)
print("\n" + "="*60)
print("📅 TEST 2: Son 60 Gün (Kasım'ı Kapsar)")
print("="*60)

try:
    opportunities2 = sam.fetch_opportunities(
        naics_codes=['721110'],
        days_back=60,
        limit=100
    )
    
    print(f"\n✅ Sonuç: {len(opportunities2)} fırsat bulundu")
    
    if opportunities2:
        # Kasım ayındaki fırsatları filtrele
        nov_opps = []
        for opp in opportunities2:
            posted_date = opp.get('postedDate', '')
            updated_date = opp.get('updatedDate', '')
            
            # Tarih parse et
            date_str = posted_date or updated_date
            if date_str:
                try:
                    # Farklı formatları dene
                    if 'T' in date_str:
                        date_str = date_str.split('T')[0]
                    date_obj = datetime.strptime(date_str[:10], '%Y-%m-%d')
                    if date_obj.month == 11 and date_obj.year == 2025:
                        nov_opps.append(opp)
                except:
                    pass
        
        print(f"\n📅 Kasım 2025'teki fırsatlar: {len(nov_opps)}")
        
        if nov_opps:
            print("\n📋 Kasım Fırsatları:")
            for i, opp in enumerate(nov_opps[:5], 1):
                notice_id = opp.get('noticeId', 'N/A')
                title = opp.get('title', 'N/A')[:60]
                posted_date = opp.get('postedDate', 'N/A')
                print(f"  {i}. {notice_id}: {title}... ({posted_date})")
        
except Exception as e:
    print(f"\n❌ Hata: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("✅ Test tamamlandı!")
print("="*60)


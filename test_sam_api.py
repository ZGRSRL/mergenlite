#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SAM.gov API Test Script"""
import os
import sys
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Windows console encoding fix
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# .env yükle
load_dotenv('mergen/.env', override=True)
api_key = os.getenv('SAM_API_KEY', '')

if not api_key:
    print("❌ SAM_API_KEY bulunamadı!")
    print("mergen/.env dosyasını kontrol edin.")
    sys.exit(1)

print(f"✅ API Key yüklendi ({len(api_key)} karakter)")

# Session oluştur
session = requests.Session()
session.headers.update({
    'User-Agent': 'MergenAI-Lite/1.0',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-API-KEY': api_key
})

base_url = "https://api.sam.gov/prod/opportunities/v2/search"

# Test 1: Notice ID ile arama - Farklı yöntemler
print("\n" + "="*60)
print("TEST 1: Notice ID ile Arama - W50S7526QA010")
print("="*60)

# Yöntem 1: noticeId parametresi ile
print("\n--- Yöntem 1: noticeId parametresi ---")
params1a = {
    'limit': 10,
    'noticeId': 'W50S7526QA010'
}

# Yöntem 2: keyword ile (tarih filtresi olmadan)
print("\n--- Yöntem 2: keyword ile (tarih filtresi olmadan) ---")
params1b = {
    'limit': 10,
    'keyword': 'W50S7526QA010'
}

# Yöntem 3: keyword ile (kısa tarih aralığı)
print("\n--- Yöntem 3: keyword ile (son 90 gün) ---")
params1c = {
    'limit': 10,
    'keyword': 'W50S7526QA010',
    'postedFrom': (datetime.now() - timedelta(days=90)).strftime('%m/%d/%Y'),
    'postedTo': datetime.now().strftime('%m/%d/%Y')
}

test_params = [
    ("noticeId parametresi", params1a),
    ("keyword (tarih yok)", params1b),
    ("keyword (90 gün)", params1c)
]

for method_name, params1 in test_params:
    print(f"\n📤 {method_name}")
    print(f"📤 Params: {params1}")
    
    try:
        response1 = session.get(base_url, params=params1, timeout=(5, 30))
        print(f"📥 Status Code: {response1.status_code}")
        
        if response1.status_code == 200:
            data1 = response1.json()
            print(f"📥 Total Records: {data1.get('totalRecords', 0)}")
            
            opportunities = data1.get('opportunitiesData', []) or data1.get('data', [])
            print(f"📥 Opportunities Found: {len(opportunities)}")
            
            if opportunities:
                print("\n✅ Sonuç bulundu:")
                for opp in opportunities[:3]:
                    print(f"  - Notice ID: {opp.get('noticeId', 'N/A')}")
                    print(f"    Opportunity ID: {opp.get('opportunityId', 'N/A')}")
                    print(f"    Title: {opp.get('title', 'N/A')[:60]}...")
                break  # Başarılı olursa diğerlerini deneme
            else:
                print("⚠️ Sonuç bulunamadı")
        else:
            print(f"❌ Hata: {response1.text[:300]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

print(f"\n📤 Request URL: {base_url}")
print(f"📤 Params: {params1}")
print(f"📤 Headers: X-API-KEY: {api_key[:8]}...")

try:
    response1 = session.get(base_url, params=params1, timeout=(5, 30))
    print(f"\n📥 Status Code: {response1.status_code}")
    print(f"📥 Headers: {dict(response1.headers)}")
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"📥 Response Keys: {list(data1.keys())}")
        print(f"📥 Total Records: {data1.get('totalRecords', 0)}")
        
        opportunities = data1.get('opportunitiesData', []) or data1.get('data', [])
        print(f"📥 Opportunities Found: {len(opportunities)}")
        
        if opportunities:
            print("\n✅ Sonuç bulundu:")
            for opp in opportunities[:3]:  # İlk 3'ü göster
                print(f"  - Notice ID: {opp.get('noticeId', 'N/A')}")
                print(f"    Opportunity ID: {opp.get('opportunityId', 'N/A')}")
                print(f"    Title: {opp.get('title', 'N/A')[:60]}...")
        else:
            print("\n⚠️ Sonuç bulunamadı")
    else:
        print(f"❌ Hata: {response1.text[:500]}")
        
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: NAICS 721110 ile arama
print("\n" + "="*60)
print("TEST 2: NAICS 721110 ile Arama (Son 30 gün)")
print("="*60)

params2 = {
    'limit': 10,
    'ncode': '721110',
    'naicsCodes': '721110',
    'postedFrom': (datetime.now() - timedelta(days=30)).strftime('%m/%d/%Y'),
    'postedTo': datetime.now().strftime('%m/%d/%Y'),
    'isActive': 'true',
    'sort': '-modifiedDate'
}

print(f"\n📤 Request URL: {base_url}")
print(f"📤 Params: {params2}")
print(f"📤 Headers: X-API-KEY: {api_key[:8]}...")

try:
    response2 = session.get(base_url, params=params2, timeout=(5, 30))
    print(f"\n📥 Status Code: {response2.status_code}")
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"📥 Response Keys: {list(data2.keys())}")
        print(f"📥 Total Records: {data2.get('totalRecords', 0)}")
        
        opportunities = data2.get('opportunitiesData', []) or data2.get('data', [])
        print(f"📥 Opportunities Found: {len(opportunities)}")
        
        if opportunities:
            print("\n✅ Sonuçlar bulundu:")
            for i, opp in enumerate(opportunities[:5], 1):  # İlk 5'i göster
                print(f"\n  {i}. Notice ID: {opp.get('noticeId', 'N/A')}")
                print(f"     Opportunity ID: {opp.get('opportunityId', 'N/A')}")
                print(f"     Title: {opp.get('title', 'N/A')[:60]}...")
                print(f"     Posted Date: {opp.get('postedDate', 'N/A')}")
        else:
            print("\n⚠️ Sonuç bulunamadı")
    elif response2.status_code == 429:
        print(f"⚠️ Rate Limit (429)")
        retry_after = response2.headers.get('Retry-After')
        if retry_after:
            print(f"   Retry-After: {retry_after}s")
        print(f"   Response: {response2.text[:500]}")
    elif response2.status_code in (401, 403):
        print(f"❌ API Key geçersiz ({response2.status_code})")
        print(f"   Response: {response2.text[:500]}")
    else:
        print(f"❌ Hata ({response2.status_code}): {response2.text[:500]}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("Test tamamlandı!")
print("="*60)


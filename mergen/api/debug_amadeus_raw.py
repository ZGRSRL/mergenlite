#!/usr/bin/env python3
"""
Debug Amadeus Raw Response for 2026 Dates
"""
import sys
import logging
from app.services.amadeus_client import search_hotels_by_city_code

# Logger ayarla
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_raw_api():
    print("🚀 Amadeus API Raw Test Başlatılıyor...")
    
    # Parametreler (Loglardan aldığımız çalışan parametreler)
    city = "HOU"
    check_in = "2026-03-03"
    check_out = "2026-03-07"
    adults = 2
    
    print(f"📋 Sorgu: {city} | {check_in} - {check_out} | Adults: {adults}")
    
    try:
        # Direkt servis fonksiyonunu çağır
        offers = search_hotels_by_city_code(city, check_in, check_out, adults)
        
        print("\n" + "="*40)
        print("📡 API YANITI")
        print("="*40)
        
        if not offers:
            print("❌ Yanıt: BOŞ LİSTE []")
            print("   Sebep: Muhtemelen tarih çok uzak (Mart 2026 > 365 gün).")
        else:
            print(f"✅ Yanıt: {len(offers)} otel bulundu.")
            if offers:
                print(f"   İlk Otel: {offers[0].get('name', 'N/A')}")
                print(f"   Fiyat: ${offers[0].get('price_per_night', 'N/A')}")
            
    except Exception as e:
        print("\n" + "="*40)
        print("🔥 API HATASI (EXCEPTION)")
        print("="*40)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_raw_api()


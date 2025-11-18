#!/usr/bin/env python3
"""
MergenLite Filtre Test - Düzeltilmiş Versiyon
NAICS ve Notice ID filtrelerinin çalışıp çalışmadığını test eder
"""

from sam_integration import SAMIntegration
import logging
import os

# .env dosyasını yükle - mergen klasöründen öncelikli
try:
    from dotenv import load_dotenv
    import os
    
    # Önce mergen klasöründeki .env dosyasını yükle
    mergen_env = 'mergen/.env'
    if os.path.exists(mergen_env):
        load_dotenv(mergen_env, override=True, verbose=False)
        print(f"[INFO] .env dosyasi yuklendi: {os.path.abspath(mergen_env)}")
    else:
        load_dotenv(override=True, verbose=False)
        print(f"[INFO] .env dosyasi yuklendi: mevcut dizin")
except ImportError:
    pass

# Logging aktif et
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_fixed_filters():
    """Düzeltilmiş filtreleri test et"""
    
    print("[TEST] MergenLite Filtre Test - Duzeltilmis Versiyon")
    print("=" * 60)
    
    # API key kontrolü
    api_key = os.getenv('SAM_API_KEY', '').strip()
    if not api_key:
        print("[HATA] SAM_API_KEY bulunamadi!")
        print("[INFO] .env dosyasinda SAM_API_KEY tanimlayin")
        return False
    
    print(f"[OK] API Key: {api_key[:10]}...{api_key[-4:]} (uzunluk: {len(api_key)})")
    
    client = SAMIntegration()
    
    # 1. NAICS 721110 Filtre Testi
    print("\n[1] NAICS 721110 Filtre Testi (Hotels & Motels)")
    print("[BEKLENEN] Sadece otel/konaklama sektorunden ilanlar")
    print("[ARAMA] Arama yapiliyor...")
    
    try:
        naics_results = client.fetch_opportunities(
            naics_codes=['721110'], 
            limit=5,
            days_back=30
        )
        
        print(f"[SONUC] {len(naics_results)} firsat bulundu")
        
        if naics_results:
            print("[LISTE] Bulunan firsatlar:")
            correct_naics_count = 0
            
            for i, opp in enumerate(naics_results[:5]):
                title = opp.get('title', 'N/A')[:50]
                naics = opp.get('naicsCode', 'N/A')
                agency = opp.get('fullParentPathName', 'N/A')[:25]
                posted = opp.get('postedDate', 'N/A')
                
                # NAICS kontrolü
                is_correct_naics = '721110' in str(naics)
                if is_correct_naics:
                    correct_naics_count += 1
                
                status_icon = "[OK]" if is_correct_naics else "[HATA]"
                print(f"   {i+1}. {status_icon} {title}...")
                print(f"      NAICS: {naics} | Kurum: {agency} | Tarih: {posted}")
            
            accuracy = (correct_naics_count / len(naics_results)) * 100
            print(f"\n[DOGRULUK] NAICS Filtre Dogrulugu: {correct_naics_count}/{len(naics_results)} ({accuracy:.1f}%)")
            
            naics_success = accuracy >= 80
        else:
            print("[HATA] NAICS 721110 icin sonuc bulunamadi")
            naics_success = False
    
    except Exception as e:
        print(f"[HATA] NAICS test hatasi: {e}")
        import traceback
        traceback.print_exc()
        naics_success = False
    
    # 2. Notice ID W50S7526QA010 Testi
    print("\n[2] Notice ID W50S7526QA010 Testi")
    print("[BEKLENEN] Spesifik ilan bulunmali")
    print("[ARAMA] Arama yapiliyor...")
    
    try:
        notice_results = client.fetch_opportunities(notice_id='W50S7526QA010')
        
        print(f"[SONUC] {len(notice_results)} firsat bulundu")
        
        if notice_results:
            opp = notice_results[0]
            print("[OK] Notice ID bulundu!")
            print(f"   Baslik: {opp.get('title')}")
            print(f"   Notice ID: {opp.get('noticeId')}")
            print(f"   Kurum: {opp.get('fullParentPathName')}")
            print(f"   NAICS: {opp.get('naicsCode')}")
            notice_success = True
        else:
            print("[HATA] Notice ID W50S7526QA010 bulunamadi")
            notice_success = False
    
    except Exception as e:
        print(f"[HATA] Notice ID test hatasi: {e}")
        import traceback
        traceback.print_exc()
        notice_success = False
    
    # 3. Genel API Sağlık Testi
    print("\n[3] Genel API Saglik Testi")
    print("[ARAMA] Genel arama yapiliyor...")
    
    try:
        general_results = client.fetch_opportunities(limit=3, days_back=7)
        print(f"[SONUC] Genel arama sonuc: {len(general_results)} firsat")
        
        if general_results:
            print("[OK] API genel olarak calisiyor")
            for i, opp in enumerate(general_results):
                print(f"   {i+1}. {opp.get('title', 'N/A')[:40]}... (NAICS: {opp.get('naicsCode', 'N/A')})")
            general_success = True
        else:
            print("[HATA] Genel API calismiyor")
            general_success = False
    
    except Exception as e:
        print(f"[HATA] Genel API test hatasi: {e}")
        import traceback
        traceback.print_exc()
        general_success = False
    
    # Sonuç özeti
    print("\n" + "=" * 60)
    print("[OZET] FILTRE TEST SONUCLARI:")
    print(f"   [OK] Genel API: {'Basarili' if general_success else 'Basarisiz'}")
    print(f"   [OK] NAICS 721110: {'Basarili' if naics_success else 'Basarisiz'}")
    print(f"   [OK] Notice ID: {'Bulundu' if notice_success else 'Bulunamadi'}")
    
    overall_success = general_success and naics_success
    
    if overall_success:
        print("\n[BASARILI] FILTRELER CALISIYOR!")
        print("[INFO] MergenLite sadeleştirmesine gecebiliriz.")
        return True
    else:
        print("\n[UYARI] BAZI FILTRELER CALISMIYOR")
        print("[INFO] API parametrelerini tekrar kontrol edin.")
        return False

if __name__ == "__main__":
    print("[BASLATILIYOR] MergenLite SAM.gov Filtre Test...")
    success = test_fixed_filters()
    print("\n[TAMAMLANDI] Test tamamlandi!")


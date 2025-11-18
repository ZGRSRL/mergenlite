#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Opportunity Attachments İndirme Testi
resourceLinks ve attachments'ları indirir
"""

import os
import sys
from pathlib import Path

def test_download_attachments(opportunity_id: str = None):
    """Attachments indirme testi"""
    print("=" * 60)
    print("Opportunity Attachments İndirme Testi")
    print("=" * 60)
    
    try:
        from backend_utils import load_opportunities_from_db, DB_AVAILABLE
        from opportunity_runner import download_from_database_raw_data
        
        if not DB_AVAILABLE:
            print("❌ [ERROR] Database bağlantısı yok")
            return False
        
        # Database'den bir opportunity yükle
        opportunities = load_opportunities_from_db(limit=1)
        
        if not opportunities:
            print("⚠️ [WARN] Database'de opportunity bulunamadı")
            print("   → Önce sync_opportunities_from_sam() çalıştırın")
            return False
        
        opp = opportunities[0]
        opp_id = opp.get('opportunityId') or opp.get('opportunity_id', 'N/A')
        notice_id = opp.get('noticeId') or opp.get('notice_id', 'N/A')
        
        print(f"📋 Test Opportunity:")
        print(f"   Opportunity ID: {opp_id}")
        print(f"   Notice ID: {notice_id}")
        print(f"   Title: {opp.get('title', 'N/A')[:60]}...")
        print()
        
        # raw_data kontrolü
        raw_data = opp.get('raw_data', {})
        if not raw_data:
            print("❌ [ERROR] raw_data boş")
            return False
        
        import json
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except:
                print("❌ [ERROR] raw_data JSON parse edilemedi")
                return False
        
        # resourceLinks ve attachments kontrolü
        resource_links = raw_data.get('resourceLinks', [])
        attachments = raw_data.get('attachments', [])
        
        total_docs = len(resource_links) + len(attachments)
        
        if total_docs == 0:
            print("⚠️ [WARN] resourceLinks ve attachments bulunamadı")
            print("   → Bu opportunity için doküman yok olabilir")
            return False
        
        print(f"📄 Dokümanlar:")
        print(f"   resourceLinks: {len(resource_links)} adet")
        print(f"   attachments: {len(attachments)} adet")
        print(f"   Toplam: {total_docs} adet")
        print()
        
        # İndirme klasörü
        download_dir = Path("downloads") / "test"
        download_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📥 İndirme başlatılıyor...")
        print(f"   Hedef klasör: {download_dir.absolute()}")
        print()
        
        # İndirme fonksiyonunu çağır
        try:
            downloaded = download_from_database_raw_data(
                opportunity_id=opp_id,
                notice_id=notice_id,
                download_dir=download_dir,
                raw_data=raw_data
            )
            
            if downloaded:
                print(f"✅ [SUCCESS] {len(downloaded)} dosya indirildi:")
                for i, file_path in enumerate(downloaded[:10], 1):  # İlk 10 dosyayı göster
                    print(f"   [{i}] {file_path.name}")
                if len(downloaded) > 10:
                    print(f"   ... ve {len(downloaded) - 10} dosya daha")
                return True
            else:
                print("⚠️ [WARN] Hiç dosya indirilemedi")
                return False
                
        except Exception as e:
            print(f"❌ [ERROR] İndirme hatası: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except ImportError as e:
        print(f"❌ [ERROR] Import hatası: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ [ERROR] Test hatası: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Komut satırı argümanı varsa kullan
    opp_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    success = test_download_attachments(opportunity_id=opp_id)
    sys.exit(0 if success else 1)

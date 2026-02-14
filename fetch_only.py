import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Path ayarı
sys.path.append(os.getcwd())

from sam_integration import SAMIntegration
from backend_utils import get_db_session
from mergenlite_models import Opportunity

load_dotenv()
API_KEY = os.getenv("SAM_API_KEY")

def fetch_and_save_only(days_back=30):
    print(f"🚜 MERGENLITE VERİ TOPLAYICI BAŞLADI (Son {days_back} Gün)")
    
    sam = SAMIntegration()
    if not sam.api_key and API_KEY:
        sam.api_key = API_KEY
    
    # 1. Verileri Çek
    print("📡 SAM.gov'dan veri çekiliyor...")
    opportunities = sam.fetch_opportunities(days_back=days_back, limit=200) # Limit artırıldı
    
    if not opportunities:
        print("📭 Hiç ilan bulunamadı.")
        return

    print(f"🌍 {len(opportunities)} adet ilan çekildi. Veritabanına aktarılıyor...")
    
    db = get_db_session()
    if not db:
        print("❌ Veritabanı bağlantısı başarısız oldu!")
        return

    new_count = 0
    skipped_count = 0

    # 2. Döngü (Sadece Kayıt)
    for opp_data in opportunities:
        # ID Belirleme
        opp_id = opp_data.get('opportunityId')
        notice_id = opp_data.get('noticeId')
        sol_num = opp_data.get('solicitationNumber')
        title = opp_data.get('title')
        primary_id = opp_id or notice_id or sol_num

        if not primary_id:
            continue

        # Veritabanı Kontrolü
        exists = None
        if opp_id:
            exists = db.query(Opportunity).filter(Opportunity.opportunity_id == opp_id).first()
        elif notice_id:
            exists = db.query(Opportunity).filter(Opportunity.notice_id == notice_id).first()
        
        if exists:
            skipped_count += 1
            if skipped_count % 10 == 0:
                print(f"   [ATLANDI] {skipped_count}. kayıt (Zaten var)")
            continue

        # Yeni Kayıt
        try:
            new_opp = Opportunity(
                opportunity_id=opp_id or primary_id,
                notice_id=notice_id,
                solicitation_number=sol_num,
                title=title,
                agency=opp_data.get('agency', ''),
                sam_gov_link=opp_data.get('samGovLink'),
                status="New", # Henüz analiz edilmedi
                raw_data=opp_data
            )
            db.add(new_opp)
            new_count += 1
            # Ekrana bilgi verelim ki ne geldiğini gör
            print(f"   [YENİ] {sol_num} - {title[:50]}...")
            
        except Exception as e:
            print(f"   ⚠️ Hata: {e}")

    try:
        db.commit()
        print("✅ Değişiklikler veritabanına kaydedildi.")
    except Exception as e:
        print(f"❌ Veritabanı kayıt hatası: {e}")
        db.rollback()
    finally:
        db.close()
    
    print("\n" + "="*40)
    print(f"🏁 İŞLEM TAMAMLANDI")
    print(f"📥 Eklenen Yeni İlan: {new_count}")
    print(f"⏩ Atlanan (Eski) İlan: {skipped_count}")
    print("="*40)

if __name__ == "__main__":
    # Konsoldan gün sayısı parametresi alabiliriz, yoksa 30 gün
    days = 30
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except:
            pass
    fetch_and_save_only(days)

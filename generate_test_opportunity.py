import os
import sys
import uuid
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Path ayarı
sys.path.append(os.getcwd())

from backend_utils import get_db_session
from mergenlite_models import Opportunity

load_dotenv()

def generate_test_opp():
    print(f"🧪 MERGENLITE TEST VERİSİ OLUŞTURUCU")
    
    db = get_db_session()
    if not db:
        print("❌ Veritabanı bağlantısı yok.")
        return

    # Random bir ID oluştur
    notice_id = f"TEST-{uuid.uuid4().hex[:8].upper()}"
    opp_id = uuid.uuid4().hex # 32 char hex
    
    title = "Test Opportunity: Emergency Generator Maintenance for disaster relief"
    
    # Gerçekçi bir raw_data simülasyonu
    raw_data = {
        "noticeId": notice_id,
        "opportunityId": opp_id,
        "title": title,
        "solicitationNumber": notice_id,
        "fullParentPathName": "DEPT OF DEFENSE",
        "postedDate": datetime.now().strftime('%Y-%m-%d'),
        "type": "Combined Synopsys/Solicitation",
        "description": "This is a synthetic test opportunity created to verify the analysis pipeline flow without hitting SAM.gov API limits. The scope includes maintenance of 500kW generators in specialized locations.",
        "naicsCode": "811310",
        "responseDeadLine": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        "resourceLinks": ["https://fake-link.com/document.pdf"]
    }

    new_opp = Opportunity(
        opportunity_id=opp_id,
        notice_id=notice_id,
        solicitation_number=notice_id,
        title=title,
        agency="Department of Testing",
        sam_gov_link=f"https://sam.gov/opp/{opp_id}/view",
        notice_type="Combined Synopsys/Solicitation",
        posted_date=datetime.now(),
        response_deadline=datetime.now() + timedelta(days=7),
        status="New", 
        raw_data=raw_data
    )

    try:
        db.add(new_opp)
        db.commit()
        print(f"✅ Test Fırsatı Oluşturuldu!")
        print(f"   Title: {title}")
        print(f"   Notice ID: {notice_id}")
        print(f"   Opportunity ID: {opp_id}")
        print("\n🚀 Şimdi Dashboard'u yenileyin, bu fırsat 'New' olarak en üstte görünecektir.")
        print(f"   Analizi başlatmak için terminaden: python run_full_analysis_pipeline.py {notice_id}")
    except Exception as e:
        print(f"❌ Hata: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_test_opp()

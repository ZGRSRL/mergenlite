"""
Ultra-Optimized SAM.gov Data Manager
Tek seferde tüm verileri çekip sonra güncelleme yapan sistem
"""

import os
import time
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

@dataclass
class FetchResult:
    """API çağrısı sonucu"""
    success: bool
    data: List[Dict] = None
    error: str = None
    total_fetched: int = 0
    total_stored: int = 0

class UltraOptimizedSAMManager:
    """Ultra optimize edilmiş SAM.gov veri yöneticisi"""
    
    def __init__(self):
        self.api_key = os.getenv('SAM_API_KEY')
        self.base_url = "https://api.sam.gov/opportunities/v2/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SAM-Ultra-Optimized/1.0',
            'Accept': 'application/json'
        })
        
        # Rate limiting - çok konservatif
        self.last_request_time = 0
        self.min_interval = 5.0  # 5 saniye bekle
        self.max_requests_per_hour = 100  # Saatte max 100 çağrı
        
        # Database connection
        self.db_conn = None
        self._connect_db()
        
        logger.info("UltraOptimizedSAMManager initialized")
    
    def _connect_db(self):
        """Veritabanına bağlan"""
        try:
            self.db_conn = psycopg2.connect(
                host='localhost',
                database='sam',
                user='postgres',
                password='postgres'
            )
            logger.info("Database connected")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            self.db_conn = None
    
    def _wait_for_rate_limit(self):
        """Rate limit için bekle"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            logger.info(f"Rate limit: {wait_time:.1f} saniye bekleniyor...")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _make_single_api_call(self, params: Dict) -> Optional[Dict]:
        """Tek API çağrısı yap"""
        try:
            self._wait_for_rate_limit()
            
            logger.info(f"API çağrısı yapılıyor: {params}")
            response = self.session.get(self.base_url, params=params, timeout=60)
            
            if response.status_code == 429:
                logger.warning("Rate limit exceeded - 60 saniye bekleniyor")
                time.sleep(60)
                return None
            
            if response.status_code == 401:
                logger.error("API key invalid")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"API çağrısı hatası: {e}")
            return None
    
    def ultra_bulk_fetch(self, days_back: int = 30, limit: int = 5000) -> FetchResult:
        """Ultra bulk fetch - tek seferde maksimum veri çek"""
        
        logger.info(f"🚀 Ultra bulk fetch başlıyor: {days_back} gün, max {limit} kayıt")
        
        # Tarih aralığı
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # API parametreleri
        params = {
            'api_key': self.api_key,
            'limit': 1000,  # Maksimum batch size
            'postedFrom': start_date.strftime('%m/%d/%Y'),
            'postedTo': end_date.strftime('%m/%d/%Y'),
            'active': 'true'
        }
        
        all_opportunities = []
        offset = 0
        batch_count = 0
        max_batches = 10  # Maksimum 10 batch (10,000 kayıt)
        
        while len(all_opportunities) < limit and batch_count < max_batches:
            batch_count += 1
            params['offset'] = offset
            
            logger.info(f"Batch {batch_count}: offset={offset}")
            
            # Tek API çağrısı
            data = self._make_single_api_call(params)
            
            if not data:
                logger.warning("API çağrısı başarısız, durduruluyor")
                break
            
            opportunities = data.get('opportunitiesData', [])
            
            if not opportunities:
                logger.info("Daha fazla veri yok")
                break
            
            # Yeni kayıtları ekle
            new_count = 0
            for opp in opportunities:
                if not any(existing.get('opportunityId') == opp.get('opportunityId') 
                          for existing in all_opportunities):
                    all_opportunities.append(opp)
                    new_count += 1
            
            logger.info(f"Batch {batch_count}: {len(opportunities)} alındı, {new_count} yeni")
            
            # Sonraki batch için offset artır
            offset += len(opportunities)
            
            # Limit kontrolü
            if len(all_opportunities) >= limit:
                break
        
        logger.info(f"📊 Toplam {len(all_opportunities)} fırsat çekildi")
        
        # Veritabanına kaydet
        stored_count = self._bulk_store_opportunities(all_opportunities)
        
        return FetchResult(
            success=True,
            data=all_opportunities,
            total_fetched=len(all_opportunities),
            total_stored=stored_count
        )
    
    def _bulk_store_opportunities(self, opportunities: List[Dict]) -> int:
        """Bulk store opportunities"""
        if not self.db_conn or not opportunities:
            return 0
        
        try:
            with self.db_conn.cursor() as cur:
                stored_count = 0
                
                for opp in opportunities:
                    try:
                        # Opportunity ID'yi al
                        opp_id = opp.get('opportunityId') or opp.get('noticeId')
                        if not opp_id:
                            continue
                        
                        # Mevcut kayıt var mı kontrol et
                        cur.execute(
                            "SELECT id FROM opportunities WHERE opportunity_id = %s",
                            (opp_id,)
                        )
                        
                        if cur.fetchone():
                            # Güncelle
                            cur.execute("""
                                UPDATE opportunities SET
                                    title = %s,
                                    description = %s,
                                    posted_date = %s,
                                    response_dead_line = %s,
                                    classification_code = %s,
                                    naics_code = %s,
                                    set_aside = %s,
                                    contract_type = %s,
                                    place_of_performance = %s,
                                    organization_type = %s,
                                    point_of_contact = %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE opportunity_id = %s
                            """, (
                                opp.get('title', ''),
                                opp.get('description', ''),
                                opp.get('postedDate'),
                                opp.get('responseDeadLine'),
                                opp.get('classificationCode'),
                                opp.get('naicsCode'),
                                opp.get('setAside'),
                                opp.get('contractType'),
                                opp.get('placeOfPerformance', {}).get('state', ''),
                                opp.get('organizationType'),
                                json.dumps(opp.get('pointOfContact', {})),
                                opp_id
                            ))
                        else:
                            # Yeni kayıt ekle
                            cur.execute("""
                                INSERT INTO opportunities (
                                    opportunity_id, title, description, posted_date,
                                    response_dead_line, classification_code, naics_code,
                                    set_aside, contract_type, place_of_performance,
                                    organization_type, point_of_contact
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                opp_id,
                                opp.get('title', ''),
                                opp.get('description', ''),
                                opp.get('postedDate'),
                                opp.get('responseDeadLine'),
                                opp.get('classificationCode'),
                                opp.get('naicsCode'),
                                opp.get('setAside'),
                                opp.get('contractType'),
                                opp.get('placeOfPerformance', {}).get('state', ''),
                                opp.get('organizationType'),
                                json.dumps(opp.get('pointOfContact', {}))
                            ))
                        
                        stored_count += 1
                        
                    except Exception as e:
                        logger.error(f"Kayıt hatası {opp.get('opportunityId', 'N/A')}: {e}")
                        continue
                
                self.db_conn.commit()
                logger.info(f"✅ {stored_count} kayıt veritabanına kaydedildi")
                return stored_count
                
        except Exception as e:
            logger.error(f"Bulk store hatası: {e}")
            if self.db_conn:
                self.db_conn.rollback()
            return 0
    
    def get_opportunity_from_db(self, notice_id: str) -> Optional[Dict]:
        """Veritabanından opportunity al (API çağrısı yapmadan)"""
        if not self.db_conn:
            return None
        
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM opportunities WHERE opportunity_id = %s",
                    (notice_id,)
                )
                result = cur.fetchone()
                
                if result:
                    logger.info(f"✅ {notice_id} veritabanından bulundu")
                    return dict(result)
                else:
                    logger.info(f"❌ {notice_id} veritabanında bulunamadı")
                    return None
                    
        except Exception as e:
            logger.error(f"Veritabanı okuma hatası: {e}")
            return None
    
    def get_documents_from_db(self, notice_id: str) -> List[Dict]:
        """Veritabanından dökümanları al (API çağrısı yapmadan)"""
        opportunity = self.get_opportunity_from_db(notice_id)
        
        if not opportunity:
            return []
        
        # Point of contact'tan resource links'i çıkar
        try:
            point_of_contact = json.loads(opportunity.get('point_of_contact', '{}'))
            resource_links = point_of_contact.get('resourceLinks', [])
            
            documents = []
            for link in resource_links:
                documents.append({
                    'description': link.get('description', 'N/A'),
                    'url': link.get('url', ''),
                    'type': link.get('type', 'N/A')
                })
            
            logger.info(f"📄 {notice_id} için {len(documents)} döküman bulundu")
            return documents
            
        except Exception as e:
            logger.error(f"Döküman parsing hatası: {e}")
            return []
    
    def update_strategy(self, days_back: int = 7) -> FetchResult:
        """Güncelleme stratejisi - sadece son X günün verilerini kontrol et"""
        logger.info(f"🔄 Güncelleme stratejisi: Son {days_back} gün")
        
        # Son güncelleme zamanını kontrol et
        last_update = self._get_last_update_time()
        
        if last_update and (datetime.now() - last_update).hours < 6:
            logger.info("Son güncelleme 6 saatten az, atlanıyor")
            return FetchResult(success=True, total_fetched=0, total_stored=0)
        
        # Sadece son X günün verilerini çek
        return self.ultra_bulk_fetch(days_back=days_back, limit=1000)
    
    def _get_last_update_time(self) -> Optional[datetime]:
        """Son güncelleme zamanını al"""
        if not self.db_conn:
            return None
        
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("SELECT MAX(updated_at) FROM opportunities")
                result = cur.fetchone()
                return result[0] if result and result[0] else None
        except Exception as e:
            logger.error(f"Son güncelleme zamanı hatası: {e}")
            return None
    
    def close(self):
        """Bağlantıları kapat"""
        if self.db_conn:
            self.db_conn.close()
        if self.session:
            self.session.close()

# Global instance
ultra_manager = UltraOptimizedSAMManager()

def ultra_bulk_fetch_and_store(days_back: int = 30, limit: int = 5000) -> Dict:
    """Ultra bulk fetch ve store"""
    result = ultra_manager.ultra_bulk_fetch(days_back, limit)
    
    return {
        'success': result.success,
        'total_fetched': result.total_fetched,
        'total_stored': result.total_stored,
        'error': result.error
    }

def get_notice_documents_optimized(notice_id: str) -> List[Dict]:
    """Optimize edilmiş döküman alma"""
    return ultra_manager.get_documents_from_db(notice_id)

def update_data_strategy() -> Dict:
    """Güncelleme stratejisi"""
    result = ultra_manager.update_strategy()
    
    return {
        'success': result.success,
        'total_fetched': result.total_fetched,
        'total_stored': result.total_stored,
        'error': result.error
    }

if __name__ == "__main__":
    # Test
    print("Ultra Optimized SAM Manager Test")
    
    # Ultra bulk fetch test
    result = ultra_bulk_fetch_and_store(days_back=7, limit=100)
    print(f"Bulk fetch: {result}")
    
    # Notice ID test
    documents = get_notice_documents_optimized("HC101325QA399")
    print(f"Documents for HC101325QA399: {len(documents)}")
    
    ultra_manager.close()

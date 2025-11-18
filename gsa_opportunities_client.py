#!/usr/bin/env python3
"""
GSA Opportunities API Client - SAM.gov Alternative
Daha iyi quota limitleri ile fırsat arama
https://open.gsa.gov/api/opportunities-api/
"""

import requests
import json
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os

# .env yükle
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GSAOpportunitiesClient:
    """GSA Opportunities API Client - SAM.gov quota bypass"""
    
    def __init__(self):
        # GSA API endpoint - SAM.gov API v2 ile uyumlu
        self.base_url = "https://api.sam.gov/opportunities/v2"
        self.description_url = "https://api.sam.gov/prod/opportunities/v1/noticedesc"
        
        # API key yükle
        self.api_key = os.getenv('SAM_API_KEY', '').strip()
        if not self.api_key:
            # Alternatif kaynaklardan dene
            self.api_key = os.environ.get('SAM_API_KEY', '').strip()
        
        # Session setup
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MergenLite/1.0 GSA-API-Client',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Rate limiting - GSA API daha esnek
        self.rate_limit_delay = 1.0  # 1 saniye (SAM.gov'dan daha hızlı)
        self.last_request_time = 0
        self.max_retries = 3
        
        logger.info(f"✅ GSA Opportunities API Client initialized")
        logger.info(f"   API Key: {'Present' if self.api_key else 'Missing'}")
    
    def _wait_for_rate_limit(self):
        """Rate limit için bekle"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def search_by_notice_id(self, notice_id: str) -> List[Dict[str, Any]]:
        """Notice ID ile direkt arama - GSA API"""
        
        notice_id = notice_id.strip()
        logger.info(f"🔍 GSA API: Notice ID araması: {notice_id}")
        
        if not self.api_key:
            logger.warning("⚠️ API key yok, boş liste döndürülüyor")
            return []
        
        self._wait_for_rate_limit()
        
        try:
            # Yöntem 1: Search API ile noticeId parametresi
            url = f"{self.base_url}/search"
            params = {
                'api_key': self.api_key,
                'noticeId': notice_id,
                'limit': 100,
                'sort': '-modifiedDate'
            }
            
            logger.info(f"GSA API Request: {url} with noticeId={notice_id}")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                opportunities = self._parse_response(data)
                
                # Notice ID ile tam eşleşenleri filtrele
                matching = [
                    opp for opp in opportunities 
                    if notice_id.upper() in str(opp.get('noticeId', '')).upper() or
                       notice_id.upper() in str(opp.get('opportunityId', '')).upper()
                ]
                
                if matching:
                    logger.info(f"✅ GSA LIVE: {len(matching)} eşleşme bulundu")
                    # Source etiketi ekle
                    for opp in matching:
                        opp['source'] = 'gsa_live'
                    return matching
                else:
                    logger.warning(f"⚠️ GSA API: Notice ID eşleşmesi bulunamadı, tüm sonuçlar: {len(opportunities)}")
            
            elif response.status_code == 429:
                logger.warning(f"⚠️ Rate limit (429), 2s bekleyip tekrar deniyor...")
                time.sleep(2)
                # Retry
                response = self.session.get(url, params=params, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    opportunities = self._parse_response(data)
                    matching = [
                        opp for opp in opportunities 
                        if notice_id.upper() in str(opp.get('noticeId', '')).upper() or
                           notice_id.upper() in str(opp.get('opportunityId', '')).upper()
                    ]
                    if matching:
                        for opp in matching:
                            opp['source'] = 'gsa_live'
                        return matching
                
                logger.warning(f"⚠️ Rate limit (429) after retry, boş liste döndürülüyor")
                return []
            
            else:
                logger.warning(f"⚠️ GSA API Error {response.status_code}, Description API deneniyor...")
                # Yöntem 2: Description API'yi dene
                desc_results = self._try_description_api(notice_id)
                if desc_results:
                    return desc_results
                # Description API de başarısız, boş liste
                logger.warning("⚠️ Description API başarısız, boş liste döndürülüyor")
                return []
        
        except Exception as e:
            logger.error(f"❌ GSA API Exception: {e}")
            return []
    
    def _try_description_api(self, notice_id: str) -> List[Dict[str, Any]]:
        """Description API ile dene"""
        try:
            self._wait_for_rate_limit()
            
            url = self.description_url
            params = {
                'noticeId': notice_id,
                'api_key': self.api_key
            }
            
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Notice data'yı opportunity formatına çevir
                if 'noticeData' in data and data['noticeData']:
                    notice_data = data['noticeData'][0]
                    
                    opportunity = {
                        'opportunityId': notice_data.get('opportunityId', notice_id),
                        'noticeId': notice_id,
                        'title': notice_data.get('title', f'Notice {notice_id}'),
                        'fullParentPathName': notice_data.get('organization', 'N/A'),
                        'postedDate': notice_data.get('postedDate', 'N/A'),
                        'responseDeadLine': notice_data.get('responseDeadLine', 'N/A'),
                        'description': notice_data.get('description', ''),
                        'naicsCode': notice_data.get('naicsCode', 'N/A'),
                        'attachments': notice_data.get('resourceLinks', []),
                        'resourceLinks': notice_data.get('resourceLinks', []),  # resourceLinks üst alana eklendi
                        'raw_data': notice_data,  # Ham veriyi koru
                        'source': 'gsa_description_api'
                    }
                    
                    logger.info(f"✅ GSA LIVE (Description API): Fırsat bulundu")
                    opportunity['source'] = 'gsa_live'
                    return [opportunity]
            
            return []
        
        except Exception as e:
            logger.error(f"Description API error: {e}")
            return []
    
    def fetch_opportunities(
        self,
        keywords: Optional[str] = None,
        naics_codes: Optional[List[str]] = None,
        days_back: int = 7,
        limit: int = 50,
        notice_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """SAMIntegration uyumlu interface"""
        
        # Notice ID ile direkt arama
        if notice_id:
            return self.search_by_notice_id(notice_id)
        
        if not self.api_key:
            logger.warning("⚠️ API key yok, boş liste döndürülüyor")
            return []
        
        # Retry mekanizması ile API çağrısı
        max_retries = 2
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                
                url = f"{self.base_url}/search"
                
                # Query parameters
                params = {
                    'api_key': self.api_key,
                    'limit': min(limit, 100),
                    'sort': '-modifiedDate'
                }
                
                # Tarih filtresi - days_back'i clamp et (min 1, max 365) ve her zaman gönder
                # GSA API dokümantasyonuna göre postedFrom/postedTo zorunlu
                days_back_clamped = max(1, min(365, days_back if days_back else 7))
                params['postedFrom'] = (datetime.now() - timedelta(days=days_back_clamped)).strftime('%m/%d/%Y')
                params['postedTo'] = datetime.now().strftime('%m/%d/%Y')
                logger.debug(f"Tarih aralığı: {params['postedFrom']} - {params['postedTo']} (days_back: {days_back} -> clamped: {days_back_clamped})")
                
                # NAICS filtresi - SADECE NAICS olarak, keyword'e EKLENMEMELİ
                if naics_codes:
                    naics_str = ','.join(naics_codes)
                    params['naicsCodes'] = naics_str
                    params['ncode'] = naics_str  # Public API uyumu için
                    logger.info(f"NAICS filtresi: {naics_codes} (naicsCodes + ncode)")
                
                # Keyword araması - SADECE kullanıcı keyword girdiyse
                if keywords and keywords.strip():
                    params['keyword'] = keywords.strip()
                    params['keywordRadio'] = 'ALL'
                    logger.info(f"Keyword filtresi: {params['keyword']}")
                else:
                    logger.info("Keyword girilmedi, sadece NAICS filtresi uygulanıyor")
            
                logger.info(f"GSA API Request (attempt {attempt + 1}/{max_retries}): {url}")
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    opportunities = self._parse_response(data)
                    logger.info(f"✅ GSA LIVE: {len(opportunities)} fırsat bulundu")
                    
                    # Source etiketi ekle
                    for opp in opportunities:
                        opp['source'] = 'gsa_live'
                    
                    return opportunities[:limit]
                
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s
                        logger.warning(f"⚠️ Rate limit (429), {wait_time}s bekleyip tekrar deniyor...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.warning(f"⚠️ Rate limit (429) after {max_retries} attempts, boş liste döndürülüyor")
                        break
                
                else:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # Exponential backoff: 1s, 2s
                        logger.warning(f"⚠️ GSA API Error {response.status_code}, {wait_time}s bekleyip tekrar deniyor...")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ GSA API Error {response.status_code} after {max_retries} attempts")
                        break
            
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"⚠️ GSA API Exception (attempt {attempt + 1}): {e}, {wait_time}s bekleyip tekrar deniyor...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"❌ GSA API Exception after {max_retries} attempts: {e}")
                    break
        
        # Tüm denemeler başarısız, boş liste döndür
        logger.warning("⚠️ GSA API başarısız, boş liste döndürülüyor")
        return []
    
    def _parse_response(self, data: Dict) -> List[Dict[str, Any]]:
        """GSA API response'unu parse et"""
        opportunities = []
        
        try:
            # SAM.gov API v2 response format
            if 'opportunitiesData' in data:
                opps_data = data['opportunitiesData']
            elif 'data' in data:
                opps_data = data['data'] if isinstance(data['data'], list) else [data['data']]
            else:
                opps_data = [data] if isinstance(data, dict) else []
            
            for opp_data in opps_data:
                opportunity = self._parse_single_opportunity(opp_data)
                if opportunity:
                    opportunities.append(opportunity)
        
        except Exception as e:
            logger.error(f"Response parsing error: {e}")
        
        return opportunities
    
    def _parse_single_opportunity(self, opp_data: Dict) -> Optional[Dict[str, Any]]:
        """Tek fırsat verisini parse et - resourceLinks ve raw_data dahil"""
        try:
            return {
                'opportunityId': opp_data.get('opportunityId', 'N/A'),
                'noticeId': opp_data.get('noticeId', opp_data.get('solicitationNumber', 'N/A')),
                'title': opp_data.get('title', 'N/A'),
                'description': opp_data.get('description', ''),
                'fullParentPathName': opp_data.get('fullParentPathName', opp_data.get('organization', 'N/A')),
                'naicsCode': opp_data.get('naicsCode', 'N/A'),
                'postedDate': opp_data.get('postedDate', 'N/A'),
                'responseDeadLine': opp_data.get('responseDeadLine', 'N/A'),
                'attachments': opp_data.get('attachments') or opp_data.get('resourceLinks', []),
                'resourceLinks': opp_data.get('resourceLinks', []),
                'raw_data': opp_data,  # Ham veriyi koru
                'source': 'gsa_api'
            }
        except Exception as e:
            logger.debug(f"Single opportunity parsing error: {e}")
            return None
    
    
    def search_by_any_id(self, id_str: str) -> List[Dict[str, Any]]:
        """Notice ID veya Opportunity ID ile akıllı arama"""
        return self.search_by_notice_id(id_str.strip())


#!/usr/bin/env python3
"""
SAM.gov API Entegrasyonu
İlan metadata ve doküman erişimi için servis
"""

import os
import requests
import time
import json
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging
from document_processor import DocumentProcessor

# .env dosyasını yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv yoksa, manuel yükleme dene
    pass

logger = logging.getLogger(__name__)

# Logging seviyesini ayarla
logging.basicConfig(level=logging.INFO)

class SAMIntegration:
    """SAM.gov API v2 entegrasyon servisi"""
    
    def __init__(self):
        # .env dosyasını yükle (mutlaka yükle) - Cache bypass için her seferinde yeniden yükle
        env_loaded = False
        try:
            from dotenv import load_dotenv
            
            # Önce mevcut environment variable'ları temizle (cache bypass)
            if 'SAM_API_KEY' in os.environ:
                del os.environ['SAM_API_KEY']
            
            # Öncelik sırası: mergen klasörü, mevcut dizin, parent dizin
            env_paths = [
                'mergen/.env',  # mergen klasörü içindeki .env (öncelikli)
                os.path.join('mergen', '.env'),  # Alternatif yol
                '.env',  # Mevcut dizin
                '../.env',  # Parent dizin
                os.path.join(os.path.dirname(__file__), '.env'),  # Script dizini
                os.path.join(os.path.dirname(__file__), 'mergen', '.env')  # Script dizini/mergen
            ]
            
            for env_path in env_paths:
                abs_path = os.path.abspath(env_path)
                if os.path.exists(env_path):
                    # Force reload - override=True ile cache'i bypass et
                    load_dotenv(env_path, override=True, verbose=True)
                    logger.info(f"✅ Loaded .env from: {abs_path} (cache bypassed)")
                    env_loaded = True
                    break
                else:
                    logger.debug(f"Not found: {abs_path}")
            
            # Eğer hiçbir yerde bulunamadıysa, tüm dizinlerde ara
            if not env_loaded:
                load_dotenv(override=True, verbose=True)
                logger.info("Attempted to load .env from current directory (cache bypassed)")
                
            # Yükleme sonrası kontrol - Fresh read
            test_key = os.getenv('SAM_API_KEY', '')
            if not test_key:
                # Direkt environment'tan oku (cache bypass)
                test_key = os.environ.get('SAM_API_KEY', '')
            
            if test_key:
                logger.info(f"✅ Environment variable SAM_API_KEY loaded: {test_key[:10]}... (length: {len(test_key)})")
            else:
                logger.warning("⚠️ SAM_API_KEY not found in environment after loading .env")
        except ImportError:
            logger.warning("python-dotenv not installed. Install with: pip install python-dotenv")
        except Exception as e:
            logger.warning(f"Error loading .env file: {e}")
        
        # API key'i yükle - tüm olası kaynaklardan
        self.api_key = ''
        
        # 1. os.getenv ile dene
        self.api_key = os.getenv('SAM_API_KEY', '').strip()
        
        # 2. os.environ ile direkt dene
        if not self.api_key:
            self.api_key = os.environ.get('SAM_API_KEY', '').strip()
        
        # 3. Streamlit secrets'den dene (eğer varsa)
        if not self.api_key:
            try:
                import streamlit as st
                if hasattr(st, 'secrets') and 'SAM_API_KEY' in st.secrets:
                    self.api_key = str(st.secrets['SAM_API_KEY']).strip()
                    logger.info("API key loaded from Streamlit secrets")
            except:
                pass
        
        # Debug bilgisi - detaylı log
        if self.api_key:
            masked_key = self.api_key[:8] + "..." + self.api_key[-4:] if len(self.api_key) > 12 else "***"
            logger.info(f"✅ API key loaded successfully (length: {len(self.api_key)}, preview: {masked_key})")
            logger.info(f"   Full API key check: {self.api_key[:30]}...{self.api_key[-10:]}")
        else:
            logger.error("❌ No API key found in any source!")
            logger.error(f"   - os.getenv('SAM_API_KEY'): {os.getenv('SAM_API_KEY', 'NOT SET')}")
            logger.error(f"   - os.environ.get('SAM_API_KEY'): {os.environ.get('SAM_API_KEY', 'NOT SET')}")
            logger.error(f"   - Current working directory: {os.getcwd()}")
            
            # Tüm olası .env dosyalarını kontrol et
            env_paths_to_check = ['.env', 'mergen/.env', '../.env']
            for env_path in env_paths_to_check:
                if os.path.exists(env_path):
                    logger.error(f"   - Found .env at: {os.path.abspath(env_path)}")
                    try:
                        with open(env_path, 'r') as f:
                            content = f.read()
                            if 'SAM_API_KEY' in content:
                                logger.error(f"   - {env_path} contains SAM_API_KEY but it's not loading!")
                                # İlk satırı göster (güvenlik için)
                                lines = content.split('\n')
                                for line in lines:
                                    if 'SAM_API_KEY' in line:
                                        logger.error(f"   - Line: {line[:50]}...")
                            else:
                                logger.error(f"   - {env_path} does not contain SAM_API_KEY")
                    except Exception as e:
                        logger.error(f"   - Error reading {env_path}: {e}")
                else:
                    logger.error(f"   - {env_path} does not exist")
        
        self.base_url = "https://api.sam.gov/opportunities/v2/search"
        self.description_base_url = "https://api.sam.gov/prod/opportunities/v1/noticedesc"
        # POST endpoint (bazı aramalar için gerekli)
        self.post_base_url = "https://api.sam.gov/opportunities/v2/search"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MergenAI-Lite/1.0',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_interval = 3.0  # 3 saniye bekle
        
        # Request timeout
        self.request_timeout = 30
        
        # Cache mekanizması (6 saat)
        self.cache_dir = Path('.cache')
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_duration = timedelta(hours=6)  # 6 saat cache
    
    def _is_opportunity_id(self, id_str: str) -> bool:
        """ID'nin Opportunity ID (public ID) mi yoksa Notice ID mi olduğunu kontrol et"""
        # Opportunity ID genellikle 32 karakterlik hex string (UUID benzeri)
        # Notice ID genellikle daha kısa ve harf-sayı karışımı (örn: W50S7526QA010)
        id_str = id_str.strip()
        
        # 32 karakterlik hex string kontrolü (opportunity ID)
        if len(id_str) == 32 and all(c in '0123456789abcdefABCDEF' for c in id_str):
            return True
        
        # UUID formatı kontrolü (tire ile ayrılmış)
        if len(id_str) == 36 and id_str.count('-') == 4:
            return True
            
        return False
    
    def _wait_for_rate_limit(self):
        """Rate limit için bekle"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_key(self, query: str) -> str:
        """Cache key oluştur"""
        key_str = f"{query}_{self.api_key[:10]}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Cache dosya yolu"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Cache'den oku"""
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
        
        try:
            # Dosya zamanını kontrol et
            file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
            if datetime.now() - file_time > self.cache_duration:
                # Cache eski, sil
                cache_path.unlink()
                logger.info(f"Cache expired for key: {cache_key}")
                return None
            
            # Cache'den oku
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"✅ Cache hit for key: {cache_key}")
                return data.get('results', [])
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None
    
    def _save_to_cache(self, cache_key: str, results: List[Dict[str, Any]]):
        """Cache'e kaydet"""
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'results': results
                }, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ Cached {len(results)} results for key: {cache_key}")
        except Exception as e:
            logger.warning(f"Error saving cache: {e}")
    
    def fetch_opportunities(
        self,
        keywords: Optional[str] = None,
        naics_codes: Optional[List[str]] = None,
        days_back: int = 7,
        limit: int = 50,
        notice_id: Optional[str] = None,
        opportunity_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Fırsatları getir"""
        
        # Notice ID ile direkt arama
        if notice_id:
            return self.fetch_by_notice_id(notice_id)
        
        # Opportunity ID ile direkt arama
        if opportunity_id:
            return self.fetch_by_opportunity_id(opportunity_id)
        
        self._wait_for_rate_limit()
        
        try:
            # Optimize edilmiş limit (önceden 100, şimdi 50)
            optimized_limit = min(limit, 50)  # Maksimum 50
            
            # Cache key oluştur
            cache_query = f"search_{keywords}_{naics_codes}_{days_back}_{optimized_limit}"
            cache_key = self._get_cache_key(cache_query)
            
            # Önce cache'den kontrol et
            cached_results = self._get_from_cache(cache_key)
            if cached_results is not None:
                return cached_results[:limit]  # İstenen limit kadar döndür
            
            # SAM.gov API v2 parametreleri - web araması ile uyumlu
            params = {
                'limit': optimized_limit,
                'postedFrom': (datetime.now() - timedelta(days=days_back)).strftime('%m/%d/%Y'),
                'postedTo': datetime.now().strftime('%m/%d/%Y'),
                'sort': '-modifiedDate',  # Web araması ile aynı sıralama
                'noticeType': 'ALL'  # Tüm ilan tipleri
            }
            
            # API key zorunlu
            if not self.api_key:
                logger.error("SAM_API_KEY is required but not found. Please set it in .env file.")
                raise ValueError("SAM_API_KEY is required. Please set it in your .env file.")
            
            params['api_key'] = self.api_key
            
            # Keyword araması - web'deki gibi
            if keywords:
                params['keyword'] = keywords
                params['keywordRadio'] = 'ALL'  # Tüm alanlarda ara (web ile uyumlu)
            
            # NAICS kodu - web'deki format ile uyumlu
            if naics_codes:
                # NAICS kodunu doğru formatta gönder
                params['naicsCode'] = ','.join(naics_codes)
                # Ayrıca serviceClassification için de ekle
                for code in naics_codes:
                    if len(code) >= 2:
                        category = code[:2]  # İlk 2 hane kategori
                        params[f'naicsCategory'] = category
            
            logger.info(f"API Request params: {dict(params)}")
            response = self.session.get(self.base_url, params=params, timeout=self.request_timeout)
            
            # HTTP status kontrolü
            if response.status_code != 200:
                logger.error(f"API returned status {response.status_code}: {response.text[:500]}")
                response.raise_for_status()
            
            data = response.json()
            logger.info(f"API Response structure: {list(data.keys())}")
            
            results = []
            if 'opportunitiesData' in data:
                results = data['opportunitiesData']
                logger.info(f"Found {len(results)} opportunities from API")
                
                # Eğer sonuç yoksa ve NAICS kodu varsa, daha geniş arama dene
                if not results and naics_codes:
                    logger.info("No results with NAICS filter, trying broader search...")
                    # NAICS filtresini kaldır, sadece keyword ile ara
                    params_no_naics = params.copy()
                    params_no_naics.pop('naicsCode', None)
                    params_no_naics.pop('naicsCategory', None)
                    
                    try:
                        response2 = self.session.get(self.base_url, params=params_no_naics, timeout=self.request_timeout)
                        if response2.status_code == 200:
                            data2 = response2.json()
                            if 'opportunitiesData' in data2:
                                results = data2['opportunitiesData']
                                logger.info(f"Found {len(results)} opportunities without NAICS filter")
                    except:
                        pass
                
                # Cache'e kaydet
                if results:
                    self._save_to_cache(cache_key, results)
                return results[:limit]  # İstenen limit kadar döndür
            else:
                logger.warning(f"API response format unexpected. Keys: {list(data.keys())}")
                logger.warning(f"Response sample: {str(data)[:500]}")
                return []
        
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"HTTP {e.response.status_code} error fetching opportunities: {e.response.text[:200]}")
            else:
                logger.error(f"HTTP error fetching opportunities: {str(e)}")
            # API hatası durumunda boş liste döndür (demo data dönme)
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching opportunities: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Error fetching opportunities: {str(e)}", exc_info=True)
            # Beklenmeyen hata durumunda boş liste döndür
            return []
    
    def search_by_any_id(self, id_str: str) -> List[Dict[str, Any]]:
        """Notice ID veya Opportunity ID ile akıllı arama"""
        
        id_str = id_str.strip()
        
        # ID tipini belirle
        if self._is_opportunity_id(id_str):
            logger.info(f"Detected Opportunity ID: {id_str}")
            return self.fetch_by_opportunity_id(id_str)
        else:
            logger.info(f"Detected Notice ID: {id_str}")
            return self.fetch_by_notice_id(id_str)
    
    def fetch_by_notice_id(self, notice_id: str) -> List[Dict[str, Any]]:
        """Notice ID ile direkt fırsat getir"""
        
        # Önce search API'de Notice ID'yi keyword olarak ara
        # SAM.gov API v2 search endpoint'i Notice ID'yi direkt desteklemiyor
        # Bu yüzden keyword araması yapıp sonuçları filtreliyoruz
        
        try:
            # Yöntem 1: Search API'de keyword araması
            self._wait_for_rate_limit()
            
            # Cache key oluştur
            cache_key = self._get_cache_key(f"notice_{notice_id}")
            
            # Önce cache'den kontrol et
            cached_results = self._get_from_cache(cache_key)
            if cached_results is not None:
                logger.info(f"✅ Notice ID {notice_id} found in cache")
                return cached_results
            
            # Optimize edilmiş limit - Notice ID araması için daha fazla sonuç al
            optimized_limit = 100  # Notice ID için daha fazla sonuç gerekebilir
            
            params = {
                'limit': optimized_limit,
                'keyword': notice_id,  # Keyword araması
                'noticeId': notice_id,  # Direkt Notice ID parametresi (SAM.gov API v2)
            }
            
            # API key zorunlu
            if not self.api_key:
                logger.error("SAM_API_KEY is required but not found. Please set it in .env file.")
                raise ValueError("SAM_API_KEY is required. Please set it in your .env file.")
            
            params['api_key'] = self.api_key
            
            # Tarih aralığını çok genişlet (son 2 yıl - 730 gün)
            # Eski ilanlar için
            params['postedFrom'] = (datetime.now() - timedelta(days=730)).strftime('%m/%d/%Y')
            params['postedTo'] = datetime.now().strftime('%m/%d/%Y')
            
            # Tarih filtresiz deneme (opsiyonel)
            logger.info(f"Searching with date range: {params['postedFrom']} to {params['postedTo']}")
            
            logger.info(f"Searching SAM.gov API for Notice ID: {notice_id} (API key: {'present' if self.api_key else 'not present'})")
            logger.info(f"API Request URL: {self.base_url}")
            logger.info(f"API Request params: {dict(params)}")
            
            response = self.session.get(self.base_url, params=params, timeout=self.request_timeout)
            
            # HTTP status kodunu kontrol et
            if response.status_code != 200:
                logger.warning(f"SAM.gov API returned status {response.status_code}: {response.text[:200]}")
                # 401 veya 403 ise API key gerekli olabilir ama devam et
                if response.status_code in [401, 403]:
                    logger.warning("API key may be required for this search")
                    # Tarih filtresiz deneme
                    params_no_date = {k: v for k, v in params.items() if k not in ['postedFrom', 'postedTo']}
                    logger.info("Retrying without date filter...")
                    try:
                        response = self.session.get(self.base_url, params=params_no_date, timeout=self.request_timeout)
                        if response.status_code == 200:
                            logger.info("Success without date filter!")
                        else:
                            response.raise_for_status()
                    except:
                        pass
            
            # 429 hatası kontrolü - özel mesaj
            if response.status_code == 429:
                try:
                    error_data = response.json()
                    next_access = error_data.get('nextAccessTime', 'Bilinmiyor')
                    logger.error(f"❌ API Quota Limit Aşıldı! Sonraki erişim: {next_access}")
                    logger.error(f"   Mesaj: {error_data.get('message', 'N/A')}")
                    logger.error(f"   Açıklama: {error_data.get('description', 'N/A')}")
                except:
                    pass
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"API Response keys: {list(data.keys())}")
            
            if 'opportunitiesData' in data:
                opportunities = data['opportunitiesData']
                logger.info(f"Found {len(opportunities)} total opportunities in API response")
                
                # İlk 5 sonucu logla (debug için)
                if opportunities:
                    logger.info("Sample opportunities:")
                    for i, opp in enumerate(opportunities[:5], 1):
                        logger.info(f"  {i}. Notice ID: {opp.get('noticeId', 'N/A')}, Title: {opp.get('title', 'N/A')[:60]}")
                
                # Notice ID ile tam eşleşenleri bul
                matching = []
                for opp in opportunities:
                    opp_notice_id = str(opp.get('noticeId', '')).strip()
                    opp_opportunity_id = str(opp.get('opportunityId', '')).strip()
                    search_id = notice_id.strip()
                    
                    # Tam eşleşme (case-insensitive)
                    if (search_id.lower() == opp_notice_id.lower() or 
                        search_id.lower() == opp_opportunity_id.lower()):
                        matching.append(opp)
                        logger.info(f"✅ Exact match found! Notice ID: {opp_notice_id}, Title: {opp.get('title', 'N/A')[:60]}")
                    # Kısmi eşleşme (Notice ID'nin bir kısmı)
                    elif (search_id in opp_notice_id or search_id in opp_opportunity_id):
                        matching.append(opp)
                        logger.info(f"⚠️ Partial match found! Notice ID: {opp_notice_id}, Title: {opp.get('title', 'N/A')[:60]}")
                
                if matching:
                    logger.info(f"✅ Found {len(matching)} matching opportunities for Notice ID: {notice_id}")
                    # Cache'e kaydet
                    self._save_to_cache(cache_key, matching)
                    return matching
                else:
                    logger.warning(f"❌ No matching opportunities found for Notice ID: {notice_id} in {len(opportunities)} results")
                    # Tüm sonuçları logla (debug için)
                    if opportunities:
                        logger.info("Available Notice IDs in response:")
                        for opp in opportunities[:10]:
                            logger.info(f"  - {opp.get('noticeId', 'N/A')}")
            else:
                logger.warning(f"API response does not contain 'opportunitiesData'. Response: {str(data)[:500]}")
            
            # Yöntem 2: Description API'yi dene
            logger.info(f"Trying description API for Notice ID: {notice_id}")
            details = self.get_opportunity_details(notice_id)
            
            if details.get('success'):
                data = details.get('data', {})
                
                # Opportunity formatına çevir
                opportunity = {
                    'opportunityId': data.get('opportunityId', notice_id),
                    'noticeId': notice_id,
                    'title': data.get('title', f'Notice {notice_id}'),
                    'fullParentPathName': data.get('organization', 'N/A'),
                    'postedDate': data.get('postedDate', 'N/A'),
                    'responseDeadLine': data.get('responseDeadLine', 'N/A'),
                    'description': data.get('description', ''),
                    'naicsCode': data.get('naicsCode', 'N/A'),
                    'attachments': data.get('attachments', [])
                }
                
                result = [opportunity]
                # Cache'e kaydet
                self._save_to_cache(cache_key, result)
                return result
            
            logger.warning(f"Could not find Notice ID: {notice_id}")
            return []
        
        except requests.exceptions.HTTPError as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                try:
                    error_body = e.response.text[:500]
                    logger.error(f"HTTP {status_code} error: {error_body}")
                    
                    # 429 hatası için özel mesaj
                    if status_code == 429:
                        try:
                            error_data = e.response.json()
                            next_access = error_data.get('nextAccessTime', 'Bilinmiyor')
                            logger.error(f"❌ API Quota Limit Aşıldı! Sonraki erişim: {next_access}")
                        except:
                            pass
                    error_msg = f"HTTP {status_code}: {error_body}"
                except:
                    error_msg = f"HTTP {status_code}: {str(e)}"
            
            if hasattr(e, 'response') and e.response and e.response.status_code == 404:
                logger.warning(f"Notice ID not found (404): {notice_id}")
            else:
                logger.error(f"HTTP error fetching Notice ID {notice_id}: {error_msg}")
            
            # Hata durumunda boş liste döndür (demo data dönme)
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching Notice ID {notice_id}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching Notice ID {notice_id}: {str(e)}", exc_info=True)
            return []
    
    def fetch_by_opportunity_id(self, opportunity_id: str) -> List[Dict[str, Any]]:
        """Opportunity ID (public ID) ile direkt arama"""
        logger.info(f"Searching by Opportunity ID: {opportunity_id}")
        
        try:
            self._wait_for_rate_limit()
            
            # API key zorunlu
            if not self.api_key:
                logger.error("SAM_API_KEY is required but not found")
                return []
            
            # Cache key oluştur
            cache_key = self._get_cache_key(f"opp_{opportunity_id}")
            
            # Önce cache'den kontrol et
            cached_results = self._get_from_cache(cache_key)
            if cached_results is not None:
                logger.info(f"✅ Opportunity ID {opportunity_id} found in cache")
                return cached_results
            
            # Yöntem 1: GET ile keyword araması
            params = {
                'limit': 50,
                'api_key': self.api_key,
                'keyword': opportunity_id,
                'postedFrom': (datetime.now() - timedelta(days=730)).strftime('%m/%d/%Y'),
                'postedTo': datetime.now().strftime('%m/%d/%Y')
            }
            
            logger.info(f"Method 1: GET search with keyword={opportunity_id}")
            try:
                response = self.session.get(self.base_url, params=params, timeout=self.request_timeout)
                response.raise_for_status()
                data = response.json()
                logger.info(f"GET Response keys: {list(data.keys())}")
            except Exception as e:
                logger.warning(f"GET method failed: {e}")
                data = {}
            
            # Yöntem 2: POST ile arama (bazı API versiyonları için)
            if 'opportunitiesData' not in data or not data.get('opportunitiesData'):
                logger.info(f"Method 2: Trying POST search")
                try:
                    payload = {
                        'api_key': self.api_key,
                        'limit': 50,
                        'keyword': opportunity_id,
                        'postedFrom': (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
                        'postedTo': datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    response = self.session.post(self.post_base_url, json=payload, timeout=self.request_timeout)
                    response.raise_for_status()
                    data = response.json()
                    logger.info(f"POST Response keys: {list(data.keys())}")
                except Exception as e:
                    logger.warning(f"POST method also failed: {e}")
                    data = {}
            
            logger.info(f"Final API Response structure: {list(data.keys()) if data else 'No data'}")
            
            if 'opportunitiesData' in data:
                opportunities = data['opportunitiesData']
                logger.info(f"Found {len(opportunities)} opportunities in response")
                
                # Opportunity ID ile tam eşleşeni bul
                search_id_lower = opportunity_id.lower()
                
                for opp in opportunities:
                    opp_id = str(opp.get('opportunityId', '')).lower()
                    notice_id = str(opp.get('noticeId', '')).lower()
                    
                    # Tam eşleşme veya kısmi eşleşme kontrolü
                    if (search_id_lower == opp_id or 
                        search_id_lower == notice_id or
                        search_id_lower in opp_id or 
                        search_id_lower in notice_id):
                        logger.info(f"Match found! Opportunity ID: {opp_id}, Notice ID: {notice_id}")
                        result = [opp]
                        # Cache'e kaydet
                        self._save_to_cache(cache_key, result)
                        return result
                
                # Eşleşme bulunamazsa, logla ve boş döndür
                logger.warning(f"No matching opportunity found for ID: {opportunity_id}")
                logger.warning(f"Available IDs in response: {[o.get('opportunityId', 'N/A')[:20] for o in opportunities[:5]]}")
                return []
            else:
                logger.warning(f"API response does not contain 'opportunitiesData'. Response: {str(data)[:500]}")
                return []
        
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"HTTP {e.response.status_code} error: {e.response.text[:200]}")
            logger.error(f"HTTP error fetching Opportunity ID {opportunity_id}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching by opportunity ID {opportunity_id}: {e}", exc_info=True)
            
            # Son çare: Description API'yi dene (eğer Notice ID ile eşleşebilirse)
            # Bazı durumlarda Opportunity ID, Notice ID'ye dönüştürülebilir
            logger.info(f"Trying alternative search methods for Opportunity ID: {opportunity_id}")
            return []
    
    def _fallback_search(self, search_id: str) -> List[Dict[str, Any]]:
        """Fallback: ID'yi keyword olarak ara"""
        
        try:
            self._wait_for_rate_limit()
            # API key zorunlu
            if not self.api_key:
                logger.error("SAM_API_KEY is required for fallback search")
                return []
            
            # Cache key oluştur
            cache_key = self._get_cache_key(f"fallback_{search_id}")
            
            # Önce cache'den kontrol et
            cached_results = self._get_from_cache(cache_key)
            if cached_results is not None:
                return cached_results
            
            # Optimize edilmiş limit (önceden 20, şimdi 10)
            params = {
                'limit': 10,
                'keyword': search_id,
                'api_key': self.api_key
            }
            
            response = self.session.get(self.base_url, params=params, timeout=self.request_timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if 'opportunitiesData' in data:
                # ID ile eşleşenleri filtrele
                search_id_lower = search_id.lower()
                matching = [
                    opp for opp in data['opportunitiesData'] 
                    if (search_id_lower in str(opp.get('opportunityId', '')).lower() 
                        or search_id_lower in str(opp.get('noticeId', '')).lower()
                        or search_id_lower in str(opp.get('title', '')).lower())
                ]
                result = matching if matching else data['opportunitiesData'][:1]
                # Cache'e kaydet
                if result:
                    self._save_to_cache(cache_key, result)
                return result
            
            return []
        
        except Exception as e2:
            logger.error(f"Fallback search also failed: {e2}")
            return []
    
    def get_opportunity_details(self, notice_id: str) -> Dict[str, Any]:
        """İlan detaylarını getir"""
        
        # API key kontrolü
        if not self.api_key:
            logger.error("SAM_API_KEY is required for get_opportunity_details")
            return {
                'success': False,
                'error': 'SAM_API_KEY is required. Please set it in your .env file.',
                'data': {}
            }
        
        self._wait_for_rate_limit()
        
        try:
            params = {
                'noticeId': notice_id,
                'api_key': self.api_key
            }
            
            response = self.session.get(self.description_base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Notice data'yı çıkar
            notice_data = {}
            if 'noticeData' in data and data['noticeData']:
                notice_data = data['noticeData'][0]
            
            # Attachment URL'lerini çıkar
            attachments = []
            resource_links = notice_data.get('resourceLinks', [])
            
            for link in resource_links:
                attachments.append({
                    'title': link.get('description', 'Attachment'),
                    'url': link.get('url', ''),
                    'type': link.get('type', 'pdf')
                })
            
            # Title ve description'ı çıkar
            title = notice_data.get('title', f'Notice {notice_id}')
            description = notice_data.get('description', '')
            
            # Eğer description yoksa, noticeData'dan diğer alanları kontrol et
            if not description:
                description = notice_data.get('additionalInfoText', '')
            
            return {
                'success': True,
                'data': {
                    'noticeId': notice_id,
                    'title': title,
                    'description': description,
                    'postedDate': notice_data.get('postedDate', 'N/A'),
                    'responseDeadLine': notice_data.get('responseDeadLine', 'N/A'),
                    'organization': notice_data.get('organization', 'N/A'),
                    'naicsCode': notice_data.get('naicsCode', 'N/A'),
                    'active': True,
                    'attachments': attachments
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting opportunity details: {e}")
            
            # Fallback: Search API'yi dene
            try:
                self._wait_for_rate_limit()
                params = {
                    'limit': 10,
                    'keyword': notice_id
                }
                
                if self.api_key:
                    params['api_key'] = self.api_key
                
                response = self.session.get(self.base_url, params=params, timeout=self.request_timeout)
                response.raise_for_status()
                
                search_data = response.json()
                
                if 'opportunitiesData' in search_data:
                    # Notice ID ile eşleşeni bul
                    for opp in search_data['opportunitiesData']:
                        if (notice_id.lower() in str(opp.get('opportunityId', '')).lower() or 
                            notice_id.lower() in str(opp.get('noticeId', '')).lower()):
                            return {
                                'success': True,
                                'data': {
                                    'noticeId': notice_id,
                                    'title': opp.get('title', f'Notice {notice_id}'),
                                    'description': opp.get('description', ''),
                                    'postedDate': opp.get('postedDate', 'N/A'),
                                    'responseDeadLine': opp.get('responseDeadLine', 'N/A'),
                                    'organization': opp.get('fullParentPathName', 'N/A'),
                                    'naicsCode': opp.get('naicsCode', 'N/A'),
                                    'active': True,
                                    'attachments': []
                                }
                            }
            
            except Exception as e2:
                logger.error(f"Fallback search also failed: {e2}")
            
            # Son çare: Mock data döndür
            return {
                'success': False,
                'error': f'Notice ID {notice_id} bulunamadı: {str(e)}',
                'data': {
                    'noticeId': notice_id,
                    'title': f'Notice {notice_id}',
                    'description': '',
                    'postedDate': 'N/A',
                    'responseDeadLine': 'N/A',
                    'organization': 'N/A',
                    'naicsCode': 'N/A',
                    'active': False,
                    'attachments': []
                }
            }
    
    def download_and_process_attachment(self, url: str, filename: str) -> Dict[str, Any]:
        """Dokümanı indir ve işle"""
        
        try:
            self._wait_for_rate_limit()
            
            # Dokümanı indir
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Geçici dosya olarak kaydet
            import tempfile
            import os
            
            file_extension = os.path.splitext(filename)[1] or '.pdf'
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
            
            try:
                # İndirilen içeriği yaz
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file.close()
                
                # DocumentProcessor ile işle
                processor = DocumentProcessor()
                result = processor.process_file_from_path(temp_file.name)
                
                # Geçici dosyayı sil
                os.unlink(temp_file.name)
                
                if result.get('success'):
                    # Filename'i ekle
                    result['data']['filename'] = filename
                    result['data']['url'] = url
                    return result
                else:
                    return result
            
            except Exception as e:
                # Hata durumunda geçici dosyayı temizle
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                raise e
        
        except Exception as e:
            logger.error(f"Error downloading attachment: {e}")
            # Fallback: Mock data döndür
            return {
                'success': True,
                'data': {
                    'filename': filename,
                    'url': url,
                    'text': f"Mock text content for {filename} (Download failed: {str(e)})",
                    'page_count': 10,
                    'file_type': 'pdf'
                }
            }
    
    def _get_mock_opportunities(self) -> List[Dict[str, Any]]:
        """Demo için mock fırsatlar"""
        return [
            {
                'opportunityId': 'DEMO-001',
                'title': 'Demo: Konaklama ve Etkinlik Hizmetleri',
                'fullParentPathName': 'Demo Organization',
                'postedDate': '2024-01-15',
                'responseDeadLine': '2024-02-15',
                'description': 'Demo açıklama metni...'
            },
            {
                'opportunityId': 'DEMO-002',
                'title': 'Demo: Toplantı ve Konferans Hizmetleri',
                'fullParentPathName': 'Demo Organization 2',
                'postedDate': '2024-01-16',
                'responseDeadLine': '2024-02-20',
                'description': 'Demo açıklama metni 2...'
            }
        ]


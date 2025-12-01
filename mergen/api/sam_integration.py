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
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta, timezone
from pathlib import Path
import logging
from email.utils import parsedate_to_datetime

logger = logging.getLogger(__name__)

# DocumentProcessor optional - sadece attachment işleme için gerekli
try:
    from document_processor import DocumentProcessor
    DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError:
    DOCUMENT_PROCESSOR_AVAILABLE = False
    DocumentProcessor = None
    logger.warning("DocumentProcessor not available, attachment processing will be limited")

# .env dosyasını yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv yoksa, manuel yükleme dene
    pass

# Logging seviyesini ayarla
logging.basicConfig(level=logging.INFO)

# SAM.gov API URL Constants
SAM_PUBLIC_SEARCH_V2 = "https://api.sam.gov/prod/opportunities/v2/search"
SAM_PUBLIC_SEARCH_V3 = "https://api.sam.gov/prod/opportunities/v3/search"
SAM_OPPORTUNITY_DETAIL_V2 = "https://api.sam.gov/prod/opportunities/v2/opportunities"
SAM_OPPORTUNITY_DETAIL_V3 = "https://api.sam.gov/prod/opportunities/v3/opportunities"
SAM_ATTACHMENT_V2 = "https://api.sam.gov/prod/opportunities/v2/attachments"
SAM_ATTACHMENT_V3 = "https://api.sam.gov/prod/opportunities/v3/attachments"
# GSA Opportunities Management API endpoints (v2/v3) - https://open.gsa.gov/api/opportunities-api/
SAM_OPPORTUNITY_V2 = "https://api.sam.gov/prod/opportunity/v2"
SAM_OPPORTUNITY_V3 = "https://api.sam.gov/prod/opportunity/v3"

class SAMIntegration:
    """SAM.gov API v2 entegrasyon servisi"""
    
    def __init__(self):
        # .env dosyasını yükle (mutlaka yükle) - Cache bypass için her seferinde yeniden yükle
        env_loaded = False
        try:
            from dotenv import load_dotenv
            
            # Environment variable'ı yedekle (cache bypass için silme, sadece yedekle)
            original_sam_key = os.environ.get('SAM_API_KEY', None)
            
            # Öncelik sırası: mergen klasörü, mevcut dizin, parent dizin
            env_paths = [
                'mergen/.env',  # mergen klasörü içindeki .env (öncelikli)
                os.path.join('mergen', '.env'),  # Alternatif yol
                '.env',  # Mevcut dizin
                '../.env',  # Parent dizin
                os.path.join(os.path.dirname(__file__), '.env'),  # Script dizini
                os.path.join(os.path.dirname(__file__), 'mergen', '.env')  # Script dizini/mergen
            ]
            
            # Öncelikle mergen/.env'yi direkt yükle
            mergen_env = 'mergen/.env'
            if os.path.exists(mergen_env):
                abs_path = os.path.abspath(mergen_env)
                load_dotenv(mergen_env, override=True, verbose=True)
                logger.info(f"[OK] Loaded .env from: {abs_path} (cache bypassed)")
                env_loaded = True
            else:
                # Diğer olası konumları kontrol et
                for env_path in env_paths:
                    if env_path == mergen_env:
                        continue  # Zaten kontrol ettik
                    abs_path = os.path.abspath(env_path)
                    if os.path.exists(env_path):
                        # Force reload - override=True ile cache'i bypass et
                        load_dotenv(env_path, override=True, verbose=True)
                        logger.info(f"[OK] Loaded .env from: {abs_path} (cache bypassed)")
                        env_loaded = True
                        break
                    else:
                        logger.debug(f"Not found: {abs_path}")
            
            # Eğer hiçbir yerde bulunamadıysa, tüm dizinlerde ara
            if not env_loaded:
                load_dotenv(override=True, verbose=True)
                logger.info("Attempted to load .env from current directory (cache bypassed)")
            
            # .env yüklenemediyse ve orijinal environment variable varsa geri koy
            if not env_loaded and original_sam_key:
                os.environ['SAM_API_KEY'] = original_sam_key
                logger.info("Restored SAM_API_KEY from original environment variable")
                
            # Yükleme sonrası kontrol - Fresh read
            test_key = os.getenv('SAM_API_KEY', '')
            if not test_key:
                # Direkt environment'tan oku (cache bypass)
                test_key = os.environ.get('SAM_API_KEY', '')
            
            if test_key:
                logger.info(f"[OK] Environment variable SAM_API_KEY loaded: {test_key[:10]}... (length: {len(test_key)})")
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
        
        # 3. Backend utils üzerinden secrets oku (Streamlit bağımlılığı olmadan)
        if not self.api_key:
            try:
                from backend_utils import get_secret
                self.api_key = get_secret('SAM_API_KEY', '').strip()
                if self.api_key:
                    logger.info("API key loaded via backend_utils.get_secret()")
            except ImportError:
                # backend_utils yoksa, Streamlit secrets'den dene (fallback)
                try:
                    import streamlit as st
                    if hasattr(st, 'secrets') and 'SAM_API_KEY' in st.secrets:
                        self.api_key = str(st.secrets['SAM_API_KEY']).strip()
                        logger.info("API key loaded from Streamlit secrets (fallback)")
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
        
        # API Version Control
        # v3 endpoint 404 hatası veriyor, v2 kullan
        self.api_version = 'v2'  # v3 404 hatası veriyor, v2'ye geç
        self.use_fallback = True  # v2 başarısızsa tekrar dene
        
        # URL'leri versiyona göre ayarla
        self._setup_urls()
        
        self.description_base_url = "https://api.sam.gov/prod/opportunities/v1/noticedesc"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MergenAI-Lite/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # X-API-KEY header'ını ekle
        if self.api_key:
            self.session.headers.update({'X-API-KEY': self.api_key})
            logger.info("✅ X-API-KEY header eklendi")
        
        # Rate limiting
        self.last_request_time = 0
        self.min_interval = 5.0  # 5 saniye bekle (artırıldı)
        self.quota_exceeded = False  # 429 hatası alındığında True
        self.quota_reset_time = None  # Quota reset zamanı
        
        # Request timeout tuple: (connect, read) in seconds
        self.request_timeout = (5, 30)
        
        # Cache mekanizması (6 saat)
        self.cache_dir = Path('.cache')
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_duration = timedelta(hours=0)  # Cache devre dışı (test için)
    
    def _setup_urls(self):
        """API versiyonuna göre URL'leri ayarla"""
        if self.api_version == 'v3':
            self.base_url = SAM_PUBLIC_SEARCH_V3
            self.post_base_url = SAM_PUBLIC_SEARCH_V3
            self.opportunity_detail_url = SAM_OPPORTUNITY_DETAIL_V3
            self.attachment_url_template = SAM_ATTACHMENT_V3
        else:
            self.base_url = SAM_PUBLIC_SEARCH_V2
            self.post_base_url = SAM_PUBLIC_SEARCH_V2
            self.opportunity_detail_url = SAM_OPPORTUNITY_DETAIL_V2
            self.attachment_url_template = SAM_ATTACHMENT_V2
            
        logger.info(f"🔄 Using SAM API {self.api_version}: {self.base_url}")
        
    def switch_to_v2(self):
        """v3'ten v2'ye geçiş yap"""
        if self.api_version == 'v3':
            logger.warning("⚠️ Switching from v3 to v2 due to error")
            self.api_version = 'v2'
            self._setup_urls()
            return True
        return False
    
    def get_api_version(self):
        """Mevcut API versiyonunu döndür"""
        return self.api_version
    
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
        # 429 hatası alındıysa, quota reset zamanını bekle
        if self.quota_exceeded and self.quota_reset_time:
            reset_time = datetime.fromisoformat(self.quota_reset_time.replace('Z', '+00:00'))
            now = datetime.now(reset_time.tzinfo)
            if now < reset_time:
                wait_seconds = (reset_time - now).total_seconds() + 10  # 10 saniye ekstra güvenlik
                logger.warning(f"⏳ Quota limit aşıldı. {wait_seconds:.0f} saniye bekleniyor (reset: {self.quota_reset_time})")
                raise ValueError(f"API quota limit aşıldı. Sonraki erişim: {self.quota_reset_time}")
        
        # Normal rate limiting
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
    
    def _fmt_mmddyyyy(self, dt: datetime) -> str:
        """Tarihi MM/dd/YYYY formatına çevir"""
        return dt.strftime("%m/%d/%Y")
    
    def _parse_opportunity(self, opp: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        API'den gelen opportunity verisini standart formata çevir
        GSA API'ye göre: Opportunity ID ve Notice ID farklı şeyler, birbirinin yerine kullanılmamalı
        """
        if not opp or not isinstance(opp, dict):
            return None
        
        try:
            # API'den gelen ham veriler
            raw_opportunity_id = opp.get('opportunityId', '').strip()
            raw_notice_id = opp.get('noticeId', '').strip()
            solicitation_number = opp.get('solicitationNumber', '').strip()
            
            # GSA API'ye göre: Opportunity ID zorunlu (32 karakter hex string)
            # Eğer yoksa, Notice ID ile detail API'den çekmeyi deneyebiliriz
            # AMA: noticeId'yi opportunityId olarak kullanmak YANLIŞ!
            
            # Önce opportunityId kontrolü
            if not raw_opportunity_id:
                # Eğer noticeId UUID formatındaysa (32 hex), bu aslında opportunityId olabilir
                # Ama bu durumda noticeId boş olmalı - API hatası olabilir
                if raw_notice_id and len(raw_notice_id) == 32 and all(c in '0123456789abcdefABCDEF' for c in raw_notice_id):
                    # Bu durumda noticeId aslında opportunityId gibi görünüyor
                    # Ama yine de noticeId'yi ayrı saklamalıyız
                    opportunity_id = raw_notice_id
                    notice_id = raw_notice_id  # Geçici olarak aynı, ama ideal değil
                    logger.warning(f"⚠️ API'den opportunityId gelmedi, noticeId UUID formatında: {raw_notice_id[:20]}...")
                else:
                    # Opportunity ID yok ve noticeId de UUID değil
                    # Bu durumda skip et veya detail API'den çek
                    logger.warning(f"⚠️ Opportunity ID bulunamadı, atlanıyor. Notice ID: {raw_notice_id}")
                    return None
            else:
                # Opportunity ID var - doğru durum
                opportunity_id = raw_opportunity_id
                notice_id = raw_notice_id or solicitation_number
            
            # SAM.gov view link oluştur
            sam_gov_link = None
            if opportunity_id and len(opportunity_id) == 32:  # Opportunity ID (32 karakter hex)
                sam_gov_link = f"https://sam.gov/opp/{opportunity_id}/view"
            elif notice_id:
                # Notice ID varsa, search URL kullan
                sam_gov_link = f"https://sam.gov/opportunities/search?noticeId={notice_id}"
            
            # Standart format - her iki ID'yi de sakla
            parsed = {
                'opportunityId': opportunity_id,  # Zorunlu - GSA Opportunity ID
                'noticeId': notice_id,  # Opsiyonel ama önemli - Notice/Solicitation Number
                'solicitationNumber': solicitation_number or notice_id,  # Solicitation Number
                'samGovLink': sam_gov_link,  # SAM.gov view link
                'title': opp.get('title', 'Başlık Yok'),
                'fullParentPathName': opp.get('fullParentPathName', opp.get('organization', 'N/A')),
                'postedDate': opp.get('postedDate', ''),
                'responseDeadLine': opp.get('responseDeadLine', ''),
                'updatedDate': opp.get('updatedDate', opp.get('modifiedDate', '')),
                'noticeType': opp.get('noticeType', ''),
                'naicsCode': opp.get('naicsCode', ''),
                'description': opp.get('description', ''),
                'attachments': opp.get('attachments', []),
                'raw_data': opp  # Orijinal veriyi de sakla
            }
            
            return parsed
        except Exception as e:
            logger.warning(f"⚠️ Opportunity parse hatası: {e}")
            return None
    
    def _sleep_until(self, next_access_time_str: str):
        """
        SAM 429 yanıtındaki nextAccessTime (UTC) alanına kadar bekler.
        Format ör.: '2025-Nov-07 00:00:00+0000 UTC'
        """
        try:
            # Kaba bir parse: 'YYYY-Mon-DD HH:MM:SS+0000 UTC'
            parts = next_access_time_str.split(" ")
            if len(parts) < 2:
                time.sleep(60)
                return
            
            # '2025-Nov-07' + '00:00:00+0000'
            date_part = parts[0]
            time_part = parts[1].split("+")[0]
            dt = datetime.strptime(f"{date_part} {time_part}", "%Y-%b-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            wait_s = max(0, int((dt - now).total_seconds()))
            if wait_s > 0:
                wait_seconds = min(wait_s, 3600)  # En fazla 1 saat bekle (korumalı)
                logger.info(f"⏳ Rate limit: {wait_seconds}s bekleniyor (nextAccessTime: {next_access_time_str})")
                time.sleep(wait_seconds)
        except Exception as e:
            logger.warning(f"nextAccessTime parse edilemedi, 60s bekleniyor: {e}")
            time.sleep(60)  # Bilinmeyen format; 1 dk. bekle
    
    def fetch_opportunities(
        self,
        keywords: Optional[Union[str, List[str]]] = None,
        naics_codes: Optional[List[str]] = None,
        days_back: int = 30,
        limit: int = 1000,
        notice_id: Optional[str] = None,
        opportunity_id: Optional[str] = None,
        page_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """Fırsatları getir - v3/v2 fallback ile"""
        
        # Notice ID ile direkt arama
        if notice_id:
            return self.fetch_by_notice_id(notice_id)
        
        # Opportunity ID ile direkt arama
        if opportunity_id:
            return self.fetch_by_opportunity_id(opportunity_id)
        
        # 429 hatası kontrolü - quota aşıldıysa hemen dur
        if self.quota_exceeded:
            logger.warning("⏸️ API quota limit aşıldı, çağrı yapılmıyor")
            return []
        
        self._wait_for_rate_limit()
        
        try:
            # Limit kontrolü (max 1000 per page)
            max_limit = min(limit, 10000)  # Toplam limit
            page_size = max(1, min(int(page_size or 1000), 1000))  # Sayfa boyutu max 1000
            
            # Cache key oluştur - NAICS kodunu da dahil et
            naics_str = ','.join(naics_codes) if naics_codes else 'none'
            cache_query = f"search_{keywords}_{naics_str}_{days_back}_{max_limit}"
            cache_key = self._get_cache_key(cache_query)
            
            # Önce cache'den kontrol et
            cached_results = self._get_from_cache(cache_key)
            if cached_results is not None:
                return cached_results[:max_limit]  # İstenen limit kadar döndür
            
            # Tarih filtresi - days_back'i clamp et (min 1, max 365) ve her zaman gönder
            # GSA API dokümantasyonuna göre postedFrom/postedTo zorunlu
            days_back_clamped = max(1, min(365, days_back if days_back else 30))
            now_utc = datetime.now(timezone.utc)
            start_date = now_utc - timedelta(days=days_back_clamped)
            
            # SAM.gov API v2 parametreleri - web araması ile uyumlu
            params = {
                'sort': '-modifiedDate',  # Web araması ile aynı sıralama
                'noticeType': 'ALL',      # Tüm ilan tipleri
                # Web aramasıyla uyum: aktif ilanlar
                'is_active': 'true',
                'isActive': 'true',
                # Tarih filtresi - ZORUNLU
                'postedFrom': self._fmt_mmddyyyy(start_date),
                'postedTo': self._fmt_mmddyyyy(now_utc)
            }
            
            logger.info(f"Tarih filtresi uygulanıyor: {params['postedFrom']} - {params['postedTo']} (days_back: {days_back} -> clamped: {days_back_clamped})")
            
            # API key zorunlu - X-API-KEY header'da zaten var, params'a ekleme
            if not self.api_key:
                logger.error("SAM_API_KEY is required but not found. Please set it in .env file.")
                raise ValueError("SAM_API_KEY is required. Please set it in your .env file.")
            
            # NOT: API key X-API-KEY header'ında gönderiliyor, params'a eklenmemeli
            
            # 721110 Default - Hotel/Motel odaklı arama
            if not naics_codes:
                naics_codes = ['721110']  # Default: Hotel/Motel
                logger.info("NAICS boş, default 721110 (Hotel/Motel) uygulanıyor")
            
            # NAICS kodu - Public API uyumu için ncode + naicsCodes
            naics_str = ','.join(naics_codes)
            params['ncode'] = naics_str  # Public API parametresi
            params['naicsCodes'] = naics_str  # Web iç arama uyumu (zararsız)
            logger.info(f"NAICS filtresi uygulanıyor: {naics_codes} (ncode + naicsCodes)")
            
            # Keyword araması - SADECE kullanıcı keyword girdiyse
            # NAICS kodu keyword olarak EKLENMEMELİ (yanlış sonuçlar getirir)
            if keywords:
                # Keywords list ise virgülle birleştir, string ise direkt kullan
                if isinstance(keywords, list):
                    keyword_str = ','.join([k.strip() for k in keywords if k.strip()])
                else:
                    keyword_str = keywords.strip() if keywords.strip() else None
                
                if keyword_str:
                    params['keyword'] = keyword_str
                    params['keywordRadio'] = 'ALL'  # Tüm alanlarda ara (web ile uyumlu)
                    logger.info(f"Keyword araması: {params['keyword']}")
                else:
                    logger.info("Keyword girilmedi, sadece NAICS filtresi uygulanıyor")
            else:
                logger.info("Keyword girilmedi, sadece NAICS filtresi uygulanıyor")
            
            # Sayfalama ile tüm sonuçları çek
            collected = []
            offset = 0
            total_records = None
            
            while len(collected) < max_limit:
                params['limit'] = page_size
                params['offset'] = offset
                
                logger.info(f"API Request (offset={offset}, limit={page_size}): {dict({k: v for k, v in params.items() if k != 'api_key'})}")
                
                try:
                    response = self.session.get(self.base_url, params=params, timeout=self.request_timeout)
                    
                    # HTTP status kod kontrolü - 401/403/429/5xx ayrımı
                    status_code = response.status_code
                    
                    if status_code == 401 or status_code == 403:
                        # API key geçersiz - tekrar deneme yapma
                        error_msg = response.text[:200] if response.text else "Unknown error"
                        logger.error(f"❌ API key geçersiz ({status_code}): {error_msg}")
                        raise ValueError(f"API key geçersiz veya yetkisiz. Status: {status_code}")
                    
                    elif status_code == 429:
                        # Rate limit - Retry-After header veya nextAccessTime kullan
                        retry_after = response.headers.get('Retry-After')
                        if retry_after:
                            try:
                                # Retry-After integer (saniye) veya HTTP date formatında olabilir
                                try:
                                    wait_seconds = int(retry_after)
                                except ValueError:
                                    # HTTP date formatı: "Sun, 09 Nov 2025 00:00:00 GMT"
                                    retry_date = parsedate_to_datetime(retry_after)
                                    now_utc = datetime.now(timezone.utc)
                                    wait_seconds = int((retry_date - now_utc).total_seconds())
                                    if wait_seconds < 0:
                                        wait_seconds = 0
                                logger.warning(f"⚠️ Rate limit (429) - Retry-After: {wait_seconds}s (next access: {retry_after})")
                                time.sleep(min(wait_seconds, 3600))  # Max 1 saat
                            except Exception as parse_error:
                                logger.warning(f"⚠️ Retry-After parse hatası: {parse_error}, 60s bekleniyor")
                                time.sleep(60)
                        else:
                            try:
                                error_data = response.json()
                                next_access = error_data.get('nextAccessTime', '')
                                logger.warning(f"⚠️ Rate limit (429) - nextAccessTime: {next_access}")
                                self._sleep_until(next_access)
                            except:
                                logger.warning("⚠️ Rate limit (429) - 60s bekleniyor")
                                time.sleep(60)
                        # 429 hatası durumunda kullanıcıya bilgi ver ve boş liste döndür
                        logger.error("❌ API Quota Limit Aşıldı! Lütfen daha sonra tekrar deneyin.")
                        return []
                    
                    elif status_code >= 500:
                        # Server hatası - exponential backoff ile retry
                        attempt_wait = min(2 ** (len(collected) // 100), 60)  # Max 60s
                        logger.warning(f"⚠️ Server error ({status_code}) - {attempt_wait}s bekleniyor")
                        time.sleep(attempt_wait)
                        continue  # Tekrar dene
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    # totalRecords + opportunitiesData beklenir
                    if total_records is None:
                        total_records = data.get("totalRecords", 0)
                        logger.info(f"📊 Toplam kayıt: {total_records}")
                    
                    items = data.get("opportunitiesData", []) or data.get("data", [])
                    collected.extend(items)
                    logger.info(f"✅ {len(items)} kayıt alındı (toplam: {len(collected)})")
                    
                    # Bitiş koşulları
                    if len(collected) >= max_limit:
                        break
                    if len(items) < page_size:
                        break  # Son sayfa
                    if total_records is not None and offset + page_size >= total_records:
                        break
                    
                    offset += page_size
                    time.sleep(0.5)  # Rate limit koruması
                    
                except requests.exceptions.HTTPError as e:
                    if e.response:
                        status_code = e.response.status_code
                        if status_code == 401 or status_code == 403:
                            error_msg = e.response.text[:200] if e.response.text else "Unknown error"
                            logger.error(f"❌ API key geçersiz ({status_code}): {error_msg}")
                            raise ValueError(f"API key geçersiz veya yetkisiz. Status: {status_code}")
                        elif status_code == 429:
                            retry_after = e.response.headers.get('Retry-After')
                            if retry_after:
                                try:
                                    # Retry-After integer (saniye) veya HTTP date formatında olabilir
                                    try:
                                        wait_seconds = int(retry_after)
                                    except ValueError:
                                        # HTTP date formatı: "Sun, 09 Nov 2025 00:00:00 GMT"
                                        retry_date = parsedate_to_datetime(retry_after)
                                        now_utc = datetime.now(timezone.utc)
                                        wait_seconds = int((retry_date - now_utc).total_seconds())
                                        if wait_seconds < 0:
                                            wait_seconds = 0
                                    logger.warning(f"⚠️ Rate limit (429) - Retry-After: {wait_seconds}s (next access: {retry_after})")
                                    time.sleep(min(wait_seconds, 3600))
                                except Exception as parse_error:
                                    logger.warning(f"⚠️ Retry-After parse hatası: {parse_error}, 60s bekleniyor")
                                    time.sleep(60)
                            else:
                                try:
                                    error_data = e.response.json()
                                    next_access = error_data.get('nextAccessTime', '')
                                    logger.warning(f"⚠️ Rate limit (429) - nextAccessTime: {next_access}")
                                    self._sleep_until(next_access)
                                except:
                                    time.sleep(60)
                            # 429 hatası durumunda kullanıcıya bilgi ver ve boş liste döndür
                            logger.error("❌ API Quota Limit Aşıldı! Lütfen daha sonra tekrar deneyin.")
                            return []
                        elif status_code >= 500:
                            attempt_wait = min(2 ** (len(collected) // 100), 60)
                            logger.warning(f"⚠️ Server error ({status_code}) - {attempt_wait}s bekleniyor")
                            time.sleep(attempt_wait)
                            continue
                    raise
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error: {str(e)}")
                    break
            
            # Üst limit kırpması
            final_items = collected[:max_limit]
            
            # Parse edilen fırsatları işle
            parsed_results = []
            for opp in final_items:
                parsed = self._parse_opportunity(opp)
                if parsed:
                    parsed['source'] = 'sam_live'
                    parsed_results.append(parsed)
            
            # Cache'e kaydet
            if parsed_results:
                self._save_to_cache(cache_key, parsed_results)
            
            logger.info(f"✅ Toplam {len(parsed_results)} fırsat bulundu (limit: {max_limit}, totalRecords: {total_records})")
            
            return parsed_results
        
        except requests.exceptions.HTTPError as e:
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"HTTP {e.response.status_code} error fetching opportunities: {e.response.text[:200]}")
            else:
                logger.error(f"HTTP error fetching opportunities: {str(e)}")
            # API hatası durumunda boş liste döndür
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching opportunities: {str(e)}")
            # Network hatasında v2'ye geçmeyi dene
            if self.use_fallback and self.switch_to_v2():
                logger.info("🔄 Network error, retrying with v2 API...")
                return self.fetch_opportunities(keywords, naics_codes, days_back, limit, notice_id, opportunity_id, page_size)
            return []
        except Exception as e:
            logger.error(f"Error fetching opportunities: {str(e)}", exc_info=True)
            # Beklenmeyen hata durumunda v2'ye geçmeyi dene
            if self.use_fallback and self.switch_to_v2():
                logger.info("🔄 Unexpected error, retrying with v2 API...")
                return self.fetch_opportunities(keywords, naics_codes, days_back, limit, notice_id, opportunity_id, page_size)
            return []
    
    def search_by_any_id(self, id_str: str) -> List[Dict[str, Any]]:
        """Notice ID, Opportunity ID veya SAM URL ile akıllı arama"""
        
        raw = id_str.strip()
        
        # URL içinden opportunityId yakala: .../opp/<32-hex>/view
        try:
            if raw.startswith('http') and '/opp/' in raw:
                import re
                m = re.search(r"/opp/([0-9a-fA-F]{32})", raw)
                if m:
                    opp_id = m.group(1)
                    logger.info(f"Extracted Opportunity ID from URL: {opp_id}")
                    return self.fetch_by_opportunity_id(opp_id)
        except Exception:
            pass
        
        # Düz ID girişi
        if self._is_opportunity_id(raw):
            logger.info(f"Detected Opportunity ID: {raw}")
            return self.fetch_by_opportunity_id(raw)
        else:
            logger.info(f"Detected Notice ID: {raw}")
            return self.fetch_by_notice_id(raw)
    
    def fetch_by_notice_id(self, notice_id: str) -> List[Dict[str, Any]]:
        """Notice ID ile direkt fırsat getir"""
        
        # 429 hatası kontrolü
        if self.quota_exceeded:
            logger.warning("⏸️ API quota limit aşıldı, çağrı yapılmıyor")
            return []
        
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
                'noticeId': notice_id,  # ✅ Direkt Notice ID parametresi (SAM.gov API v2)
                # Keyword parametresi Notice ID aramasında gerekli değil, sadece noticeId yeterli
            }
            
            # API key zorunlu
            if not self.api_key:
                logger.error("SAM_API_KEY is required but not found. Please set it in .env file.")
                raise ValueError("SAM_API_KEY is required. Please set it in your .env file.")
            
            # NOT: API key X-API-KEY header'ında gönderiliyor, params'a eklenmemeli
            
            # Tarih aralığını makul bir süreye ayarla (1 yıl - 365 gün)
            # API tarih formatı: MM/dd/yyyy
            params['postedFrom'] = (datetime.now() - timedelta(days=365)).strftime('%m/%d/%Y')
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
            
            # 429 hatası kontrolü
            if response.status_code == 429:
                try:
                    error_data = response.json()
                    self.quota_reset_time = error_data.get('nextAccessTime', '')
                    self.quota_exceeded = True
                    next_access = error_data.get('nextAccessTime', 'Bilinmiyor')
                    logger.error(f"❌ API Quota Limit Aşıldı! Sonraki erişim: {next_access}")
                    logger.error(f"   Mesaj: {error_data.get('message', 'N/A')}")
                    logger.error(f"   Açıklama: {error_data.get('description', 'N/A')}")
                    return []
                except:
                    pass
                # 429 hatası alındı, boş liste döndür
                return []
            
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
                    # Her opportunity'ye raw_data ekle (resourceLinks korunması için)
                    for opp in matching:
                        if 'raw_data' not in opp:
                            opp['raw_data'] = opp.copy()  # Kendi kopyasını raw_data olarak ekle
                        # resourceLinks kontrolü
                        if 'resourceLinks' not in opp and 'attachments' in opp:
                            opp['resourceLinks'] = opp.get('attachments', [])
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
                
                # Opportunity formatına çevir - resourceLinks dahil
                attachments = data.get('attachments', [])
                resource_links = data.get('resourceLinks', attachments)  # resourceLinks varsa onu kullan
                
                opportunity = {
                    'opportunityId': data.get('opportunityId', notice_id),
                    'noticeId': notice_id,
                    'title': data.get('title', f'Notice {notice_id}'),
                    'fullParentPathName': data.get('organization', 'N/A'),
                    'postedDate': data.get('postedDate', 'N/A'),
                    'responseDeadLine': data.get('responseDeadLine', 'N/A'),
                    'description': data.get('description', ''),
                    'naicsCode': data.get('naicsCode', 'N/A'),
                    'attachments': attachments,
                    'resourceLinks': resource_links,  # GSA API dokümantasyonuna göre resourceLinks mevcut
                    'raw_data': data  # Ham veriyi koru
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
            
            # Hata durumunda boş liste döndür
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
        
        # 429 hatası kontrolü
        if self.quota_exceeded:
            logger.warning("⏸️ API quota limit aşıldı, çağrı yapılmıyor")
            return []
        
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
                # NOT: API key X-API-KEY header'ında gönderiliyor
                'keyword': opportunity_id,
                'postedFrom': (datetime.now() - timedelta(days=730)).strftime('%m/%d/%Y'),
                'postedTo': datetime.now().strftime('%m/%d/%Y')
            }
            
            logger.info(f"GET search with keyword={opportunity_id}")
            try:
                response = self.session.get(self.base_url, params=params, timeout=self.request_timeout)
                
                # 429 hatası kontrolü
                if response.status_code == 429:
                    try:
                        error_data = response.json()
                        self.quota_reset_time = error_data.get('nextAccessTime', '')
                        self.quota_exceeded = True
                        logger.error(f"❌ API Quota Limit Aşıldı! Sonraki erişim: {self.quota_reset_time}")
                        return []
                    except:
                        return []
                
                response.raise_for_status()
                data = response.json()
                logger.info(f"GET Response keys: {list(data.keys())}")
            except Exception as e:
                logger.warning(f"GET method failed: {e}")
                data = {}
            
            # POST request kaldırıldı - Gereksiz çift çağrı yapıyordu
            # Sadece GET request kullan
            
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
                        # raw_data ekle (resourceLinks korunması için)
                        if 'raw_data' not in opp:
                            opp['raw_data'] = opp.copy()  # Kendi kopyasını raw_data olarak ekle
                        # resourceLinks kontrolü
                        if 'resourceLinks' not in opp and 'attachments' in opp:
                            opp['resourceLinks'] = opp.get('attachments', [])
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
    
    def download_documents(self, notice_id: str, dest_dir: str = "downloads") -> List[Dict[str, Any]]:
        """Dokümanları indir ve kaydet - Geliştirilmiş: Attachments API kullan"""
        import os
        from pathlib import Path
        
        dest_path = Path(dest_dir)
        dest_path.mkdir(exist_ok=True)
        
        downloaded = []
        
        try:
            # Önce detayları al
            details = self.get_opportunity_details(notice_id)
            if not details.get('success'):
                logger.warning(f"⚠️ Notice ID {notice_id} detayları alınamadı: {details.get('error', 'Unknown error')}")
                # Detaylar alınamazsa bile attachments API'yi dene
            else:
                attachments = details.get('data', {}).get('attachments', [])
                if attachments:
                    logger.info(f"✅ {len(attachments)} attachment bulundu (get_opportunity_details'den)")
                    for attachment in attachments:
                        url = attachment.get('url')
                        title = attachment.get('title', 'attachment')
                        file_type = attachment.get('type', 'pdf')
                        
                        if url:
                            try:
                                result = self.download_and_process_attachment(url, title, dest_dir=str(dest_path))
                                if result.get('success'):
                                    downloaded.append({
                                        'filename': result['data'].get('filename', title),
                                        'path': result['data'].get('file_path', ''),
                                        'text': result['data'].get('text', ''),
                                        'page_count': result['data'].get('page_count', 0),
                                        'url': url,
                                        'title': title,
                                        'type': file_type
                                    })
                            except Exception as e:
                                logger.error(f"❌ Attachment indirme hatası {title}: {e}")
            
            # Alternatif: GSA Opportunities API v2/v3 ile attachments metadata al
            if not downloaded:
                logger.info(f"🔄 GSA Opportunities API ile attachments metadata alınıyor: {notice_id}")
                try:
                    import re
                    is_opportunity_id = re.fullmatch(r"[0-9a-fA-F]{32}", notice_id)
                    
                    if is_opportunity_id:
                        # GSA Opportunities API v3: Download Metadata for All Attachments by Opportunity ID
                        # GET /prod/opportunity/v3/{opportunityId}/attachments/metadata
                        endpoints_to_try = [
                            (f"{SAM_OPPORTUNITY_V3}/{notice_id}/attachments/metadata", 'v3 metadata'),
                            (f"{SAM_OPPORTUNITY_V2}/{notice_id}/attachments/metadata", 'v2 metadata'),
                            (SAM_ATTACHMENT_V3, 'v3 attachments'),
                            (SAM_ATTACHMENT_V2, 'v2 attachments')
                        ]
                    else:
                        # Notice ID ile deneme
                        endpoints_to_try = [
                            (SAM_ATTACHMENT_V3, 'v3 attachments'),
                            (SAM_ATTACHMENT_V2, 'v2 attachments')
                        ]
                    
                    for endpoint_url, version in endpoints_to_try:
                        try:
                            params = {}
                            if not is_opportunity_id and 'metadata' not in endpoint_url:
                                params['noticeId'] = notice_id
                            
                            self._wait_for_rate_limit()
                            response = self.session.get(endpoint_url, params=params, timeout=30)
                            
                            if response.status_code == 200:
                                data = response.json()
                                
                                # Farklı response formatlarını kontrol et
                                attachments_data = (
                                    data.get('attachments', []) or 
                                    data.get('data', []) or 
                                    data.get('attachmentList', []) or
                                    data.get('attachmentMetadataList', []) or
                                    (data if isinstance(data, list) else [])
                                )
                                
                                if attachments_data:
                                    logger.info(f"✅ {len(attachments_data)} attachment metadata bulundu (GSA API {version}'den)")
                                    
                                    for att in attachments_data:
                                        # Metadata'dan URL oluştur veya direkt URL al
                                        resource_id = att.get('resourceId') or att.get('resourceID') or att.get('id')
                                        attachment_id = att.get('attachmentId') or att.get('attachmentID')
                                        
                                        # URL oluştur: Download Attachment as Original File Type
                                        # GET /prod/opportunity/v3/{opportunityId}/attachments/{resourceId}
                                        if resource_id and is_opportunity_id:
                                            download_url = f"{SAM_OPPORTUNITY_V3}/{notice_id}/attachments/{resource_id}"
                                        elif attachment_id and is_opportunity_id:
                                            download_url = f"{SAM_OPPORTUNITY_V3}/{notice_id}/attachments/{attachment_id}"
                                        else:
                                            # Direkt URL varsa kullan
                                            download_url = att.get('url') or att.get('downloadUrl') or att.get('link') or att.get('href')
                                        
                                        title = (
                                            att.get('title') or 
                                            att.get('name') or 
                                            att.get('description') or 
                                            att.get('fileName') or 
                                            att.get('resourceName') or 
                                            'attachment'
                                        )
                                        file_type = att.get('type') or att.get('fileType') or att.get('mimeType') or att.get('contentType', 'pdf')
                                        
                                        if download_url:
                                            try:
                                                result = self.download_and_process_attachment(download_url, title, dest_dir=str(dest_path))
                                                if result.get('success'):
                                                    downloaded.append({
                                                        'filename': result['data'].get('filename', title),
                                                        'path': result['data'].get('file_path', ''),
                                                        'text': result['data'].get('text', ''),
                                                        'page_count': result['data'].get('page_count', 0),
                                                        'url': download_url,
                                                        'title': title,
                                                        'type': file_type
                                                    })
                                                    logger.info(f"✅ İndirildi ve işlendi: {title}")
                                            except Exception as e:
                                                logger.error(f"❌ Attachment indirme hatası {title}: {e}")
                                    break  # Başarılı olduysa diğer endpoint'i deneme
                            elif response.status_code != 404:
                                logger.warning(f"⚠️ GSA API {version} hatası: {response.status_code} - {response.text[:200]}")
                        except Exception as e:
                            logger.warning(f"⚠️ GSA API {version} çağrısı başarısız: {e}")
                            continue
                except Exception as e:
                    logger.warning(f"⚠️ GSA Opportunities API genel hatası: {e}")
            
            # Son çare: Description'ı döküman olarak kullan (MUTLAKA bir şey döndürmeli)
            if not downloaded:
                logger.info(f"🔄 Attachments bulunamadı, description'ı döküman olarak kullanıyorum: {notice_id}")
                try:
                    details = self.get_opportunity_details(notice_id)
                    if details.get('success'):
                        description = details.get('data', {}).get('description', '')
                        title = details.get('data', {}).get('title', '')
                        additional_info = details.get('data', {}).get('additionalInfoText', '')
                        
                        # Tüm metinleri birleştir
                        combined_text = ""
                        if title:
                            combined_text += f"{title}\n\n"
                        if description:
                            combined_text += f"{description}\n\n"
                        if additional_info:
                            combined_text += f"{additional_info}\n\n"
                        
                        combined_text = combined_text.strip()
                        
                        if combined_text:
                            # Description'ı dosya olarak kaydet
                            desc_file = dest_path / 'opportunity_description.txt'
                            with open(desc_file, 'w', encoding='utf-8') as f:
                                f.write(combined_text)
                            
                            # Description'ı döküman olarak ekle
                            downloaded.append({
                                'filename': 'opportunity_description.txt',
                                'path': str(desc_file),
                                'text': combined_text,
                                'page_count': max(1, len(combined_text) // 2000),  # Yaklaşık sayfa sayısı
                                'url': '',
                                'title': 'Opportunity Description',
                                'type': 'text'
                            })
                            logger.info(f"✅ Description döküman olarak kaydedildi: {desc_file} ({len(combined_text)} karakter)")
                        else:
                            logger.warning(f"⚠️ Description da boş: {notice_id}")
                    else:
                        logger.warning(f"⚠️ Opportunity details alınamadı: {details.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.error(f"❌ Description alma hatası: {e}", exc_info=True)
            
            # Eğer hala döküman yoksa, uyarı ver ama boş liste döndürme
            if not downloaded:
                logger.error(f"❌ {notice_id} için hiç döküman bulunamadı. Opportunity ID veya Notice ID formatını kontrol edin.")
        
        except Exception as e:
            logger.error(f"❌ Döküman indirme genel hatası: {e}", exc_info=True)
            # Hata durumunda bile description'ı dene
            try:
                details = self.get_opportunity_details(notice_id)
                if details.get('success'):
                    description = details.get('data', {}).get('description', '')
                    title = details.get('data', {}).get('title', '')
                    if description or title:
                        combined_text = f"{title}\n\n{description}".strip()
                        if combined_text:
                            # Description'ı dosya olarak kaydet
                            desc_file = dest_path / 'opportunity_description_fallback.txt'
                            with open(desc_file, 'w', encoding='utf-8') as f:
                                f.write(combined_text)
                            
                            downloaded.append({
                                'filename': 'opportunity_description_fallback.txt',
                                'path': str(desc_file),
                                'text': combined_text,
                                'page_count': 1,
                                'url': '',
                                'title': 'Opportunity Description (Fallback)',
                                'type': 'text'
                            })
            except Exception as e:
                logger.warning(f"⚠️ Fallback description kaydetme hatası: {e}")
        
        return downloaded
    
    def get_opportunity_details(self, notice_id: str) -> Dict[str, Any]:
        """İlan detaylarını getir - birden çok parametre adıyla dene"""
        
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
            # Olası parametre adlarını sırayla dene
            param_candidates = []
            # Öncelik: noticeId (genelde solicitation number)
            param_candidates.append({'noticeId': notice_id})
            # Alternatif: solicitationNumber anahtarı
            param_candidates.append({'solicitationNumber': notice_id})
            # Opportunity ID gibi görünüyor mu? 32-hex ise farklı anahtarlarla dene
            try:
                import re
                if re.fullmatch(r"[0-9a-fA-F]{32}", notice_id):
                    param_candidates.append({'opportunityId': notice_id})
                    param_candidates.append({'oppId': notice_id})
            except Exception:
                pass

            data = None
            notice_data = None
            last_error = None
            for p in param_candidates:
                params = {}  # NOT: API key X-API-KEY header'ında gönderiliyor
                params.update(p)
                try:
                    response = self.session.get(self.description_base_url, params=params, timeout=30)
                    response.raise_for_status()
                    d = response.json()
                    if 'noticeData' in d and d['noticeData']:
                        data = d
                        notice_data = d['noticeData'][0]
                        logger.info(f"noticedesc success with params {p}")
                        break
                    else:
                        last_error = f"Empty noticeData with params {p}"
                except Exception as ie:
                    last_error = str(ie)
                    continue
            if data is None or notice_data is None:
                raise RuntimeError(last_error or 'No data from noticedesc')
            
            # Attachment URL'lerini çıkar - Geliştirilmiş: Birden fazla kaynaktan
            attachments = []
            
            # 1. resourceLinks'ten (eski format) - String array veya object array olabilir
            resource_links = notice_data.get('resourceLinks', [])
            if resource_links:
                for link in resource_links:
                    # Eğer link string ise (URL direkt), object değilse
                    if isinstance(link, str):
                        attachments.append({
                            'title': f'Attachment {len(attachments) + 1}',
                            'url': link,
                            'type': 'pdf'  # Default
                        })
                    else:
                        # Object ise
                        url = link.get('url') or link.get('link') or link.get('downloadUrl') or link.get('href')
                        if url:
                            attachments.append({
                                'title': link.get('description') or link.get('title') or link.get('name', f'Attachment {len(attachments) + 1}'),
                                'url': url,
                                'type': link.get('type') or link.get('fileType', 'pdf')
                            })
            
            # 2. attachments array'inden (yeni format)
            if 'attachments' in notice_data:
                for att in notice_data.get('attachments', []):
                    if isinstance(att, str):
                        attachments.append({
                            'title': f'Attachment {len(attachments) + 1}',
                            'url': att,
                            'type': 'pdf'
                        })
                    else:
                        url = att.get('url') or att.get('link') or att.get('downloadUrl')
                        if url:
                            attachments.append({
                                'title': att.get('title') or att.get('name') or att.get('description', f'Attachment {len(attachments) + 1}'),
                                'url': url,
                                'type': att.get('type') or att.get('fileType', 'pdf')
                            })
            
            # 3. documents array'inden
            if 'documents' in notice_data:
                for doc in notice_data.get('documents', []):
                    if isinstance(doc, str):
                        attachments.append({
                            'title': f'Document {len(attachments) + 1}',
                            'url': doc,
                            'type': 'pdf'
                        })
                    else:
                        url = doc.get('url') or doc.get('link') or doc.get('downloadUrl')
                        if url:
                            attachments.append({
                                'title': doc.get('title') or doc.get('name') or doc.get('description', f'Document {len(attachments) + 1}'),
                                'url': url,
                                'type': doc.get('type') or doc.get('fileType', 'pdf')
                            })
            
            logger.info(f"📎 {len(attachments)} attachment bulundu (get_opportunity_details'den - noticedesc)")
            
            # Eğer attachments bulunamadıysa, SAM.gov Attachments API'yi dene
            if not attachments:
                logger.info(f"🔄 Attachments API'den çekiliyor: {notice_id}")
                try:
                    import re
                    is_opportunity_id = re.fullmatch(r"[0-9a-fA-F]{32}", notice_id)
                    
                    if is_opportunity_id:
                        # Opportunity ID ile attachments metadata al
                        # GET /prod/opportunity/v3/{opportunityId}/attachments/metadata
                        endpoints_to_try = [
                            (f"{SAM_OPPORTUNITY_V3}/{notice_id}/attachments/metadata", 'v3 metadata'),
                            (f"{SAM_OPPORTUNITY_V2}/{notice_id}/attachments/metadata", 'v2 metadata')
                        ]
                    else:
                        # Notice ID ile attachments al
                        endpoints_to_try = [
                            (SAM_ATTACHMENT_V3, 'v3 attachments'),
                            (SAM_ATTACHMENT_V2, 'v2 attachments')
                        ]
                    
                    for endpoint_url, version in endpoints_to_try:
                        try:
                            params = {}
                            if not is_opportunity_id and 'metadata' not in endpoint_url:
                                params['noticeId'] = notice_id
                            
                            self._wait_for_rate_limit()
                            response = self.session.get(endpoint_url, params=params, timeout=30)
                            
                            if response.status_code == 200:
                                data = response.json()
                                
                                # Farklı response formatlarını kontrol et
                                attachments_data = (
                                    data.get('attachments', []) or 
                                    data.get('data', []) or 
                                    data.get('attachmentList', []) or
                                    data.get('attachmentMetadataList', []) or
                                    (data if isinstance(data, list) else [])
                                )
                                
                                if attachments_data:
                                    logger.info(f"✅ {len(attachments_data)} attachment metadata bulundu (Attachments API {version}'den)")
                                    
                                    for att in attachments_data:
                                        # Metadata'dan URL oluştur veya direkt URL al
                                        resource_id = att.get('resourceId') or att.get('resourceID') or att.get('id')
                                        attachment_id = att.get('attachmentId') or att.get('attachmentID')
                                        
                                        # URL oluştur: Download Attachment as Original File Type
                                        if resource_id and is_opportunity_id:
                                            download_url = f"{SAM_OPPORTUNITY_V3}/{notice_id}/attachments/{resource_id}"
                                        elif attachment_id and is_opportunity_id:
                                            download_url = f"{SAM_OPPORTUNITY_V3}/{notice_id}/attachments/{attachment_id}"
                                        else:
                                            # Direkt URL varsa kullan
                                            download_url = att.get('url') or att.get('downloadUrl') or att.get('link') or att.get('href')
                                        
                                        title = (
                                            att.get('title') or 
                                            att.get('name') or 
                                            att.get('description') or 
                                            att.get('fileName') or 
                                            att.get('resourceName') or 
                                            'attachment'
                                        )
                                        file_type = att.get('type') or att.get('fileType') or att.get('mimeType') or att.get('contentType', 'pdf')
                                        
                                        if download_url:
                                            attachments.append({
                                                'title': title,
                                                'url': download_url,
                                                'type': file_type
                                            })
                                    break  # Başarılı olduysa diğer endpoint'i deneme
                            elif response.status_code != 404:
                                logger.debug(f"⚠️ Attachments API {version} hatası: {response.status_code}")
                        except Exception as e:
                            logger.debug(f"⚠️ Attachments API {version} çağrısı başarısız: {e}")
                            continue
                except Exception as e:
                    logger.debug(f"⚠️ Attachments API genel hatası: {e}")
            
            logger.info(f"📎 Toplam {len(attachments)} attachment bulundu (get_opportunity_details)")
            
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
                    'attachments': attachments,
                    'resourceLinks': attachments  # resourceLinks olarak da ekle (geriye uyumluluk için)
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting opportunity details: {e}")
            
            # Hata durumunda boş sonuç döndür
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
    
    def download_and_process_attachment(self, url: str, filename: str, dest_dir: Optional[str] = None) -> Dict[str, Any]:
        """Dokümanı indir, kaydet ve işle"""
        from pathlib import Path
        
        try:
            self._wait_for_rate_limit()
            
            # Dokümanı indir
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Hedef klasör
            if dest_dir:
                dest_path = Path(dest_dir)
                dest_path.mkdir(parents=True, exist_ok=True)
                
                # Dosya adını temizle
                safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                if not safe_filename.endswith(('.pdf', '.docx', '.doc', '.txt')):
                    safe_filename += '.pdf'
                
                target_file = dest_path / safe_filename
            else:
                # Geçici dosya kullan
                import tempfile
                import os
                file_extension = os.path.splitext(filename)[1] or '.pdf'
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_extension)
                target_file = Path(temp_file.name)
                temp_file.close()
            
            # İndirilen içeriği yaz
            with open(target_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Dosya indirildi: {target_file} ({target_file.stat().st_size} bytes)")
            
            # DocumentProcessor ile işle (eğer mevcut ise)
            if DOCUMENT_PROCESSOR_AVAILABLE and DocumentProcessor:
                processor = DocumentProcessor()
                result = processor.process_file_from_path(str(target_file))
            else:
                # DocumentProcessor yoksa basit sonuç döndür
                result = {
                    'success': True,
                    'data': {
                        'filename': target_file.name,
                        'path': str(target_file),
                        'size': target_file.stat().st_size,
                        'text': '',  # DocumentProcessor olmadan metin çıkarımı yapılamaz
                        'page_count': 0
                    }
                }
            
            # Geçici dosya ise sil
            if not dest_dir:
                try:
                    target_file.unlink()
                except:
                    pass
            
            if result.get('success'):
                # Filename ve path'i ekle
                result['data']['filename'] = safe_filename if dest_dir else filename
                result['data']['file_path'] = str(target_file) if dest_dir else ''
                result['data']['url'] = url
                return result
            else:
                return result
        
        except Exception as e:
            logger.error(f"Error downloading attachment: {e}", exc_info=True)
            # Hata durumunda boş sonuç döndür
            return {
                'success': False,
                'error': f'Document processing failed: {str(e)}'
            }

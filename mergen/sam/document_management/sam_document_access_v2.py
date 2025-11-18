"""
SAM.gov API v2 Döküman Erişim Sistemi
Description ve ResourceLinks erişimi için optimize edilmiş sistem
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
class DocumentInfo:
    """Döküman bilgisi"""
    title: str
    url: str
    type: str
    description: str = ""
    size: int = 0
    source: str = ""

@dataclass
class OpportunityDescription:
    """Fırsat açıklaması"""
    notice_id: str
    description_url: str
    content: str = ""
    success: bool = False
    error: str = ""

class SAMDocumentAccessManager:
    """SAM.gov API v2 döküman erişim yöneticisi"""
    
    def __init__(self):
        self.api_key = os.getenv('SAM_API_KEY')
        self.base_url = "https://api.sam.gov/opportunities/v2/search"
        self.description_base_url = "https://api.sam.gov/prod/opportunities/v1/noticedesc"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SAM-Document-Access/1.0',
            'Accept': 'application/json'
        })
        
        # Rate limiting - çok konservatif
        self.last_request_time = 0
        self.min_interval = 3.0  # 3 saniye bekle
        
        # Database connection
        self.db_conn = None
        self._connect_db()
        
        logger.info("SAMDocumentAccessManager initialized")
    
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
    
    def get_opportunity_description(self, notice_id: str) -> OpportunityDescription:
        """Fırsat açıklamasını al (API v2 description URL ile)"""
        
        logger.info(f"Description alınıyor: {notice_id}")
        
        # Önce veritabanından description URL'ini al
        description_url = self._get_description_url_from_db(notice_id)
        
        if not description_url:
            logger.warning(f"Description URL bulunamadı: {notice_id}")
            return OpportunityDescription(
                notice_id=notice_id,
                description_url="",
                success=False,
                error="Description URL not found in database"
            )
        
        # API key ile description URL'ine erişim
        try:
            self._wait_for_rate_limit()
            
            params = {
                'api_key': self.api_key,
                'noticeid': notice_id
            }
            
            logger.info(f"Description API çağrısı: {notice_id}")
            response = self.session.get(description_url, params=params, timeout=30)
            
            if response.status_code == 200:
                content = response.text
                logger.info(f"✅ Description başarıyla alındı: {notice_id}")
                
                return OpportunityDescription(
                    notice_id=notice_id,
                    description_url=description_url,
                    content=content,
                    success=True
                )
            elif response.status_code == 404:
                logger.warning(f"Description bulunamadı: {notice_id}")
                return OpportunityDescription(
                    notice_id=notice_id,
                    description_url=description_url,
                    success=False,
                    error="Description Not Found"
                )
            else:
                logger.error(f"Description API hatası: {response.status_code}")
                return OpportunityDescription(
                    notice_id=notice_id,
                    description_url=description_url,
                    success=False,
                    error=f"API Error: {response.status_code}"
                )
                
        except Exception as e:
            logger.error(f"Description erişim hatası: {e}")
            return OpportunityDescription(
                notice_id=notice_id,
                description_url=description_url,
                success=False,
                error=str(e)
            )
    
    def get_opportunity_resource_links(self, notice_id: str) -> List[DocumentInfo]:
        """ResourceLinks array'inden dökümanları al"""
        
        logger.info(f"ResourceLinks alınıyor: {notice_id}")
        
        # Veritabanından resourceLinks'i al
        resource_links = self._get_resource_links_from_db(notice_id)
        
        if not resource_links:
            logger.warning(f"ResourceLinks bulunamadı: {notice_id}")
            return []
        
        documents = []
        
        for i, link in enumerate(resource_links):
            try:
                # Link'i parse et
                if isinstance(link, str):
                    url = link
                    title = f"Document {i+1}"
                    doc_type = self._get_file_type_from_url(url)
                elif isinstance(link, dict):
                    url = link.get('url', '')
                    title = link.get('description', f"Document {i+1}")
                    doc_type = link.get('type', self._get_file_type_from_url(url))
                else:
                    continue
                
                if not url:
                    continue
                
                # Döküman bilgisini oluştur
                doc_info = DocumentInfo(
                    title=title,
                    url=url,
                    type=doc_type,
                    description=f"Resource link {i+1}",
                    source="resourceLinks"
                )
                
                documents.append(doc_info)
                
            except Exception as e:
                logger.error(f"Resource link parsing hatası: {e}")
                continue
        
        logger.info(f"✅ {len(documents)} resource link bulundu: {notice_id}")
        return documents
    
    def get_opportunity_documents_complete(self, notice_id: str) -> Dict[str, Any]:
        """Tam döküman erişimi (description + resourceLinks)"""
        
        logger.info(f"Tam döküman erişimi başlıyor: {notice_id}")
        
        result = {
            'notice_id': notice_id,
            'description': None,
            'resource_links': [],
            'total_documents': 0,
            'success': False,
            'error': None
        }
        
        try:
            # 1. Description al
            description = self.get_opportunity_description(notice_id)
            result['description'] = description
            
            # 2. ResourceLinks al
            resource_links = self.get_opportunity_resource_links(notice_id)
            result['resource_links'] = resource_links
            
            # 3. Toplam döküman sayısı
            total_docs = 1 if description.success else 0
            total_docs += len(resource_links)
            result['total_documents'] = total_docs
            
            # 4. Başarı durumu
            result['success'] = description.success or len(resource_links) > 0
            
            logger.info(f"✅ Tam döküman erişimi tamamlandı: {notice_id} - {total_docs} döküman")
            
        except Exception as e:
            logger.error(f"Tam döküman erişim hatası: {e}")
            result['error'] = str(e)
        
        return result
    
    def _get_description_url_from_db(self, notice_id: str) -> Optional[str]:
        """Veritabanından description URL'ini al"""
        if not self.db_conn:
            return None
        
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT point_of_contact FROM opportunities WHERE opportunity_id = %s",
                    (notice_id,)
                )
                result = cur.fetchone()
                
                if result and result['point_of_contact']:
                    point_of_contact = json.loads(result['point_of_contact'])
                    return point_of_contact.get('description')
                
                return None
                
        except Exception as e:
            logger.error(f"Description URL veritabanı hatası: {e}")
            return None
    
    def _get_resource_links_from_db(self, notice_id: str) -> List[Any]:
        """Veritabanından resourceLinks'i al"""
        if not self.db_conn:
            return []
        
        try:
            with self.db_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT point_of_contact FROM opportunities WHERE opportunity_id = %s",
                    (notice_id,)
                )
                result = cur.fetchone()
                
                if result and result['point_of_contact']:
                    point_of_contact = json.loads(result['point_of_contact'])
                    return point_of_contact.get('resourceLinks', [])
                
                return []
                
        except Exception as e:
            logger.error(f"ResourceLinks veritabanı hatası: {e}")
            return []
    
    def _get_file_type_from_url(self, url: str) -> str:
        """URL'den dosya tipini çıkar"""
        if not url:
            return "unknown"
        
        url_lower = url.lower()
        
        if '.pdf' in url_lower:
            return "PDF"
        elif '.doc' in url_lower or '.docx' in url_lower:
            return "Word Document"
        elif '.xls' in url_lower or '.xlsx' in url_lower:
            return "Excel Spreadsheet"
        elif '.txt' in url_lower:
            return "Text File"
        elif '.zip' in url_lower:
            return "ZIP Archive"
        elif '.jpg' in url_lower or '.jpeg' in url_lower:
            return "JPEG Image"
        elif '.png' in url_lower:
            return "PNG Image"
        else:
            return "Unknown"
    
    def download_document(self, document_info: DocumentInfo, download_dir: Path) -> Dict[str, Any]:
        """Dökümanı indir"""
        
        try:
            # İndirme klasörünü oluştur
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Dosya adını oluştur
            filename = self._create_filename(document_info)
            file_path = download_dir / filename
            
            # Rate limiting
            self._wait_for_rate_limit()
            
            # İndirme
            logger.info(f"Döküman indiriliyor: {document_info.url}")
            response = self.session.get(document_info.url, timeout=60)
            
            if response.status_code == 200:
                # Dosyayı kaydet
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                file_size = file_path.stat().st_size
                
                logger.info(f"✅ Döküman indirildi: {filename} ({file_size} bytes)")
                
                return {
                    'success': True,
                    'filename': filename,
                    'file_path': str(file_path),
                    'file_size': file_size,
                    'error': None
                }
            else:
                logger.error(f"Döküman indirme hatası: {response.status_code}")
                return {
                    'success': False,
                    'filename': filename,
                    'file_path': None,
                    'file_size': 0,
                    'error': f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Döküman indirme hatası: {e}")
            return {
                'success': False,
                'filename': document_info.title,
                'file_path': None,
                'file_size': 0,
                'error': str(e)
            }
    
    def _create_filename(self, document_info: DocumentInfo) -> str:
        """Dosya adı oluştur"""
        # Güvenli dosya adı oluştur
        safe_title = "".join(c for c in document_info.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')
        
        # Dosya uzantısını ekle
        if document_info.type == "PDF":
            ext = ".pdf"
        elif document_info.type == "Word Document":
            ext = ".docx"
        elif document_info.type == "Excel Spreadsheet":
            ext = ".xlsx"
        elif document_info.type == "Text File":
            ext = ".txt"
        elif document_info.type == "ZIP Archive":
            ext = ".zip"
        else:
            ext = ".bin"
        
        return f"{safe_title}{ext}"
    
    def close(self):
        """Bağlantıları kapat"""
        if self.db_conn:
            self.db_conn.close()
        if self.session:
            self.session.close()

# Global instance
document_access_manager = SAMDocumentAccessManager()

def get_opportunity_description_v2(notice_id: str) -> Dict[str, Any]:
    """API v2 ile fırsat açıklaması al"""
    description = document_access_manager.get_opportunity_description(notice_id)
    
    return {
        'notice_id': description.notice_id,
        'description_url': description.description_url,
        'content': description.content,
        'success': description.success,
        'error': description.error
    }

def get_opportunity_resource_links_v2(notice_id: str) -> List[Dict[str, Any]]:
    """API v2 ile resourceLinks al"""
    documents = document_access_manager.get_opportunity_resource_links(notice_id)
    
    return [
        {
            'title': doc.title,
            'url': doc.url,
            'type': doc.type,
            'description': doc.description,
            'source': doc.source
        }
        for doc in documents
    ]

def get_opportunity_documents_complete_v2(notice_id: str) -> Dict[str, Any]:
    """API v2 ile tam döküman erişimi"""
    return document_access_manager.get_opportunity_documents_complete(notice_id)

# SAM Collector Functions (moved from sam_collector.py)

def fetch_opportunities(keywords: List[str] = None, naics_codes: List[str] = None, 
                       days_back: int = 7, limit: int = 100) -> Dict[str, Any]:
    """SAM.gov'dan fırsatları topla"""
    
    logger.info(f"Fırsat toplama başlıyor: keywords={keywords}, naics={naics_codes}, days={days_back}, limit={limit}")
    
    result = {
        'success': False,
        'opportunities': [],
        'count': 0,
        'error': None
    }
    
    try:
        # Tarih aralığını hesapla
        posted_date_from = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # API payload'ı hazırla
        payload = {
            'api_key': document_access_manager.api_key,
            'limit': limit,
            'postedFrom': posted_date_from,
            'sortBy': 'modifiedDate',
            'sortOrder': 'desc'
        }
        
        # Filtreleme kriterleri
        if keywords:
            payload['keyword'] = keywords
        
        if naics_codes:
            payload['naicsCodes'] = naics_codes
        
        # Rate limiting
        document_access_manager._wait_for_rate_limit()
        
        # API çağrısı
        logger.info(f"API çağrısı yapılıyor: {document_access_manager.base_url}")
        response = document_access_manager.session.post(document_access_manager.base_url, json=payload, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            
            opportunities = data.get('opportunitiesData', [])
            result['opportunities'] = opportunities
            result['count'] = len(opportunities)
            result['success'] = True
            
            logger.info(f"✅ {len(opportunities)} fırsat toplandı")
            
        else:
            result['error'] = f"API Error: {response.status_code} - {response.text}"
            logger.error(f"API hatası: {response.status_code}")
    
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Fırsat toplama hatası: {e}")
    
    return result

def get_opportunity_details(notice_id: str) -> Dict[str, Any]:
    """Belirli bir fırsatın detaylarını al"""
    
    logger.info(f"Fırsat detayları alınıyor: {notice_id}")
    
    result = {
        'success': False,
        'opportunity': None,
        'attachments': [],
        'error': None
    }
    
    try:
        # Rate limiting
        document_access_manager._wait_for_rate_limit()
        
        # API çağrısı için basit payload
        payload = {
            'api_key': document_access_manager.api_key,
            'noticeId': notice_id
        }
        
        response = document_access_manager.session.post(document_access_manager.base_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            opportunities = data.get('opportunitiesData', [])
            
            if opportunities:
                opp = opportunities[0]
                result['opportunity'] = opp
                result['success'] = True
                
                logger.info(f"✅ Fırsat detayları API'den alındı: {notice_id}")
            else:
                result['error'] = "Fırsat bulunamadı"
        else:
            result['error'] = f"API Error: {response.status_code}"
    
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Fırsat detayları alma hatası: {e}")
    
    return result

def download_all_attachments(notice_id: str) -> Dict[str, Any]:
    """Bir fırsatın tüm eklerini indir"""
    
    logger.info(f"Ekler indiriliyor: {notice_id}")
    
    result = {
        'success': False,
        'downloaded': 0,
        'failed': 0,
        'error': None
    }
    
    try:
        # Fırsat detaylarını al
        details_result = get_opportunity_details(notice_id)
        
        if not details_result['success']:
            result['error'] = details_result['error']
            return result
        
        opportunity = details_result['opportunity']
        
        # ResourceLinks'i al
        resource_links = document_access_manager.get_opportunity_resource_links(notice_id)
        
        if not resource_links:
            result['error'] = "Ek bulunamadı"
            return result
        
        # İndirme klasörü
        download_dir = Path('downloads') / notice_id
        
        downloaded_count = 0
        failed_count = 0
        
        for doc_info in resource_links:
            try:
                # İndir
                download_result = document_access_manager.download_document(doc_info, download_dir)
                
                if download_result['success']:
                    downloaded_count += 1
                else:
                    failed_count += 1
                    logger.error(f"Ek indirme hatası: {download_result['error']}")
            
            except Exception as e:
                failed_count += 1
                logger.error(f"Ek indirme hatası: {e}")
        
        result['success'] = True
        result['downloaded'] = downloaded_count
        result['failed'] = failed_count
        
        logger.info(f"✅ Ek indirme tamamlandı: {downloaded_count} başarılı, {failed_count} başarısız")
    
    except Exception as e:
        result['error'] = str(e)
    return result

if __name__ == "__main__":
    # Test
    print("SAM.gov API v2 Document Access Test")
    
    # Test notice ID
    test_notice_id = "HC101325QA399"
    
    # Description test
    description = get_opportunity_description_v2(test_notice_id)
    print(f"Description: {description}")
    
    # ResourceLinks test
    resource_links = get_opportunity_resource_links_v2(test_notice_id)
    print(f"ResourceLinks: {len(resource_links)}")
    
    # Complete test
    complete = get_opportunity_documents_complete_v2(test_notice_id)
    print(f"Complete: {complete}")
    
    # SAM Collector functions test
    print("\nTesting SAM Collector functions:")
    
    # Fetch opportunities test
    opportunities = fetch_opportunities(keywords=["hotel", "lodging"], days_back=7, limit=5)
    print(f"Fetched opportunities: {opportunities['count']}")
    
    # Get opportunity details test
    details = get_opportunity_details(test_notice_id)
    print(f"Opportunity details: {details['success']}")
    
    # Download attachments test (commented out to avoid actual downloads)
    # download_result = download_all_attachments(test_notice_id)
    # print(f"Download result: {download_result}")
    
    document_access_manager.close()

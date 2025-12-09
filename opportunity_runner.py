#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MergenLite Opportunity Runner
Fırsat koduna göre otomatik klasör oluşturma, döküman indirme ve analiz orkestrasyonu
"""

import os
import logging
import requests
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from both root and mergen/.env
load_dotenv()
load_dotenv(dotenv_path='mergen/.env')

# Local imports
try:
    from sam_integration import SAMIntegration
    SAM_INTEGRATION_AVAILABLE = True
except ImportError:
    SAM_INTEGRATION_AVAILABLE = False
    logging.warning("SAM integration not available")

from mergenlite_opportunity_pipeline import run_mergen_opportunity_analysis

logger = logging.getLogger(__name__)

def sanitize_code(code: str) -> str:
    """Fırsat kodunu güvenli klasör adına çevir"""
    return "".join(c for c in code.strip() if c.isalnum() or c in ("_", "-"))

def prepare_opportunity_folder(base_dir: str, opportunity_code: str) -> Path:
    """Fırsat klasörünü oluştur"""
    code = sanitize_code(opportunity_code)
    folder = Path(base_dir) / "opportunities" / code
    folder.mkdir(parents=True, exist_ok=True)
    logger.info(f"[Folder] Created/verified: {folder}")
    return folder

def extract_zip_to_folder(zip_path: Path, dest_folder: Path) -> List[Path]:
    """
    ZIP dosyasını belirtilen klasöre ayıkla
    
    Args:
        zip_path: ZIP dosyasının yolu
        dest_folder: Ayıklama hedef klasörü
    
    Returns:
        Ayıklanan dosya yolları listesi
    """
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # ZIP içindeki tüm dosyaları listele
            file_list = zip_ref.namelist()
            
            for file_name in file_list:
                # Güvenlik: Path traversal saldırılarına karşı kontrol
                if '..' in file_name or file_name.startswith('/'):
                    logger.warning(f"[ZIP] Güvenlik: Şüpheli dosya adı atlandı: {file_name}")
                    continue
                
                # Sadece desteklenen formatları ayıkla
                file_ext = Path(file_name).suffix.lower()
                if file_ext not in ['.pdf', '.docx', '.doc', '.txt', '.xls', '.xlsx']:
                    continue
                
                try:
                    # Dosya yolunu güvenli hale getir
                    safe_name = Path(file_name).name  # Sadece dosya adını al
                    target_path = dest_folder / safe_name
                    
                    # Aynı isimde dosya varsa, ZIP adını prefix olarak ekle
                    if target_path.exists():
                        zip_name = zip_path.stem
                        target_path = dest_folder / f"{zip_name}_{safe_name}"
                    
                    # Dosyayı ayıkla
                    with zip_ref.open(file_name) as source, open(target_path, 'wb') as target:
                        target.write(source.read())
                    
                    extracted_files.append(target_path)
                    logger.info(f"[ZIP] Ayıklandı: {safe_name} -> {target_path}")
                
                except Exception as e:
                    logger.warning(f"[ZIP] {file_name} ayıklanırken hata: {e}")
                    continue
        
        return extracted_files
    
    except Exception as e:
        logger.error(f"[ZIP] ZIP ayıklama hatası {zip_path}: {e}")
        return []

def detect_document_type(name: str, text: str = "") -> str:
    """Dosya adı ve içeriğe göre belge tipini tespit et"""
    lname = name.lower()
    text_lower = text.lower() if text else ""
    
    # RFQ
    if "rfq" in lname or "request_for_quote" in lname or "request for quote" in lname:
        return "rfq"
    
    # SOW
    if "sow" in lname or "statement of work" in lname or "statement_of_work" in lname:
        return "sow"
    
    # Contract
    if any(keyword in lname for keyword in ["signed", "award", "contract", "agreement"]):
        return "contract"
    
    # Compliance / FAR
    if "far_52.204.24" in lname or "52.204-24" in lname or "52.204-25" in lname or "52.204-26" in lname:
        return "compliance"
    if text and ("52.204-24" in text_lower or "52.204-25" in text_lower or "52.204-26" in text_lower):
        return "compliance"
    
    # Past Performance
    if "past_performance" in lname or "past performance" in lname or "performance" in lname:
        return "performance"
    
    return "general"

def download_documents(
    folder: Path, 
    documents: List[Dict[str, str]], 
    skip_existing: bool = True
) -> List[Dict[str, Any]]:
    """
    Dökümanları indir ve belge tipini tespit et
    
    Args:
        folder: Hedef klasör
        documents: [{"url": "...", "name": "..."}, ...]
        skip_existing: Mevcut dosyaları atla
    
    Returns:
        İndirilen döküman bilgileri listesi
    """
    downloaded = []
    seen_urls = set()  # Duplicate URL engelleme için
    
    for doc in documents:
        url = doc.get("url", "")
        
        # Duplicate URL kontrolü
        if not url:
            logger.warning(f"[Skip] Empty URL, skipping document: {doc.get('name', 'unknown')}")
            continue
        
        # URL'yi normalize et (query string'leri kaldır, lowercase)
        url_normalized = url.split('?')[0].lower().strip()
        if url_normalized in seen_urls:
            logger.info(f"[Skip] Duplicate URL detected, skipping: {url[:50]}...")
            continue
        seen_urls.add(url_normalized)
        
        name = doc.get("name") or doc.get("filename") or url.split("/")[-1].split("?")[0]
        
        # Dosya uzantısını kontrol et
        if not any(name.lower().endswith(ext) for ext in ('.pdf', '.docx', '.doc', '.txt', '.zip', '.xls', '.xlsx')):
            # URL'den uzantıyı çıkar
            url_ext = Path(url.split('?')[0]).suffix.lower()
            if url_ext in ('.pdf', '.docx', '.doc', '.txt', '.zip', '.xls', '.xlsx'):
                name = name + url_ext if not name.endswith(url_ext) else name
            else:
                name += '.pdf'  # Default extension
        
        target = folder / name
        
        # Mevcut dosyayı atla (idempotent)
        if skip_existing and target.exists() and target.stat().st_size > 0:
            logger.info(f"[Skip] File already exists: {name}")
            downloaded.append({
                "name": name,
                "path": str(target),
                "document_type": detect_document_type(name),
                "status": "existing"
            })
            continue
        
        # İndir
        try:
            logger.info(f"[Download] {name} from {url[:50]}...")
            resp = requests.get(url, timeout=60, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            resp.raise_for_status()
            
            with open(target, "wb") as f:
                f.write(resp.content)
            
            # ZIP dosyası ise ayıkla
            if name.lower().endswith('.zip'):
                extracted = extract_zip_to_folder(target, folder)
                if extracted:
                    logger.info(f"[ZIP] {len(extracted)} dosya ayıklandı: {name}")
                    # Ayıklanan dosyaları da ekle
                    for ext_file in extracted:
                        doc_type = detect_document_type(ext_file.name)
                        downloaded.append({
                            "name": ext_file.name,
                            "path": str(ext_file),
                            "document_type": doc_type,
                            "status": "extracted_from_zip",
                            "size": ext_file.stat().st_size,
                            "source_zip": name
                        })
                    # ZIP dosyasını da ekle (opsiyonel, istenirse kaldırılabilir)
                    downloaded.append({
                        "name": name,
                        "path": str(target),
                        "document_type": "zip",
                        "status": "downloaded",
                        "size": target.stat().st_size
                    })
                else:
                    logger.warning(f"[ZIP] {name} ayıklanamadı veya içinde döküman yok")
                    downloaded.append({
                        "name": name,
                        "path": str(target),
                        "document_type": "zip",
                        "status": "downloaded_no_extract",
                        "size": target.stat().st_size
                    })
            else:
                # Normal dosya
                doc_type = detect_document_type(name)
                
                downloaded.append({
                    "name": name,
                    "path": str(target),
                    "document_type": doc_type,
                    "status": "downloaded",
                    "size": target.stat().st_size
                })
            
            logger.info(f"[OK] Downloaded: {name}")
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to download {name}: {e}")
            continue
    
    return downloaded

def download_from_database_raw_data(
    folder: Path,
    notice_id: str,
    opportunity_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Database'deki raw_data'dan resourceLinks çıkar ve dökümanları indir
    (SAM.gov API'ye bağlı değil, direkt URL'lerden indirir)
    
    Args:
        folder: Hedef klasör
        notice_id: SAM.gov Notice ID
        opportunity_id: Optional Opportunity ID
    
    Returns:
        İndirilen döküman bilgileri listesi
    """
    try:
        from backend_utils import get_db_session
        from mergenlite_models import Opportunity
        import json
        
        db = get_db_session()
        if not db:
            logger.warning("[WARNING] Database session not available")
            return []
        
        try:
            # Opportunity'yi bul (notice_id veya opportunity_id ile)
            opp = None
            if opportunity_id:
                opp = db.query(Opportunity).filter(
                    Opportunity.opportunity_id == opportunity_id
                ).first()
            
            if not opp and notice_id:
                opp = db.query(Opportunity).filter(
                    Opportunity.notice_id == notice_id
                ).first()
            
            if not opp or not opp.raw_data:
                logger.warning(f"[Database] Opportunity not found or no raw_data: {notice_id}")
                return []
            
            # raw_data'yı parse et
            raw_data = opp.raw_data
            if isinstance(raw_data, str):
                try:
                    raw_data = json.loads(raw_data)
                except json.JSONDecodeError:
                    logger.warning(f"[Database] Invalid raw_data JSON: {notice_id}")
                    return []
            
            # resourceLinks'i çıkar
            resource_links = raw_data.get('resourceLinks', [])
            attachments = raw_data.get('attachments', [])
            documents = raw_data.get('documents', [])
            
            # Tüm URL'leri topla
            urls_to_download = []
            
            # 1. resourceLinks
            for link in resource_links:
                if isinstance(link, str):
                    urls_to_download.append({'url': link, 'title': f'Document {len(urls_to_download) + 1}'})
                elif isinstance(link, dict):
                    url = link.get('url') or link.get('link') or link.get('downloadUrl') or link.get('href')
                    if url:
                        urls_to_download.append({
                            'url': url,
                            'title': link.get('title') or link.get('name') or link.get('description', f'Document {len(urls_to_download) + 1}')
                        })
            
            # 2. attachments
            for att in attachments:
                if isinstance(att, str):
                    urls_to_download.append({'url': att, 'title': f'Attachment {len(urls_to_download) + 1}'})
                elif isinstance(att, dict):
                    url = att.get('url') or att.get('link') or att.get('downloadUrl')
                    if url:
                        urls_to_download.append({
                            'url': url,
                            'title': att.get('title') or att.get('name') or att.get('description', f'Attachment {len(urls_to_download) + 1}')
                        })
            
            # 3. documents
            for doc in documents:
                if isinstance(doc, str):
                    urls_to_download.append({'url': doc, 'title': f'Document {len(urls_to_download) + 1}'})
                elif isinstance(doc, dict):
                    url = doc.get('url') or doc.get('link') or doc.get('downloadUrl')
                    if url:
                        urls_to_download.append({
                            'url': url,
                            'title': doc.get('title') or doc.get('name') or doc.get('description', f'Document {len(urls_to_download) + 1}')
                        })
            
            if not urls_to_download:
                logger.warning(f"[Database] No resourceLinks/attachments found in raw_data: {notice_id}")
                return []
            
            logger.info(f"[Database] Found {len(urls_to_download)} document URL(s) in raw_data")
            
            # URL'lerden direkt indir (SAM.gov API'ye bağlı değil)
            result = download_documents(folder, urls_to_download)
            
            # Belge tipini tespit et ve metadata ekle
            processed = []
            for doc_info in result:
                file_path = doc_info.get('path', '')
                
                # VALIDATION: Dosya var mı ve boyutu > 0 mı?
                if not file_path or not Path(file_path).exists() or Path(file_path).stat().st_size == 0:
                    logger.warning(f"[Database] Skipped empty/missing file: {file_path}")
                    continue

                filename = doc_info.get('name', Path(file_path).name if file_path else 'document.pdf')
                
                # Dosyayı işle
                try:
                    from document_processor import DocumentProcessor
                    processor = DocumentProcessor()
                    process_result = processor.process_file_from_path(file_path)
                    if process_result.get('success'):
                        text = process_result['data'].get('text', '')
                        page_count = process_result['data'].get('page_count', 0)
                    else:
                        text = ''
                        page_count = 0
                except Exception:
                    text = ''
                    page_count = 0
                
                doc_type = detect_document_type(filename, text)
                
                processed.append({
                    "name": filename,
                    "path": file_path,
                    "document_type": doc_type,
                    "status": "downloaded_from_database",
                    "text": text,
                    "page_count": page_count
                })
            
            logger.info(f"[Database] Downloaded and validated {len(processed)} document(s) from raw_data URLs")
            return processed
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[ERROR] Database raw_data download error: {e}", exc_info=True)
        return []

def download_from_sam(
    folder: Path,
    notice_id: str,
    opportunity_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    SAM.gov'dan dökümanları indir
    Önce database'deki raw_data'dan resourceLinks'i dener, başarısız olursa SAM.gov API'yi kullanır
    
    Args:
        folder: Hedef klasör
        notice_id: SAM.gov Notice ID
        opportunity_id: Optional Opportunity ID
    
    Returns:
        İndirilen döküman bilgileri listesi
    """
    # Önce database'deki raw_data'dan resourceLinks'i dene (API quota limiti yok)
    logger.info(f"[Step 2a] Trying to download from database raw_data (resourceLinks)...")
    downloaded = download_from_database_raw_data(folder, notice_id, opportunity_id)
    
    if downloaded:
        logger.info(f"[OK] Downloaded {len(downloaded)} document(s) from database raw_data")
        return downloaded
    
    # Database'den indirilemediyse, SAM.gov API'yi dene
    if not SAM_INTEGRATION_AVAILABLE:
        logger.warning("[WARNING] SAM integration not available")
        return []
    
    try:
        sam = SAMIntegration()
        
        logger.info(f"[Step 2b] Trying SAM.gov API...")
        # Dökümanları indir
        downloaded = sam.download_documents(notice_id, dest_dir=str(folder))
        
        # Opportunity ID ile de dene
        if not downloaded and opportunity_id and opportunity_id != notice_id:
            logger.info(f"[SAM.gov] Trying with Opportunity ID: {opportunity_id}")
            downloaded = sam.download_documents(opportunity_id, dest_dir=str(folder))
        
        if not downloaded:
            logger.warning(f"[SAM.gov] No documents found for {notice_id}")
            return []
        
        # Belge tipini tespit et ve metadata ekle
        result = []
        for doc_info in downloaded:
            file_path = doc_info.get('path') or doc_info.get('file_path', '')
            
            # VALIDATION: Dosya var mı ve boyutu > 0 mı?
            if not file_path or not Path(file_path).exists() or Path(file_path).stat().st_size == 0:
                logger.warning(f"[SAM.gov] Skipped empty/missing file: {file_path}")
                continue

            filename = doc_info.get('filename', Path(file_path).name if file_path else 'document.pdf')
            text = doc_info.get('text', '')
            
            doc_type = detect_document_type(filename, text)
            
            result.append({
                "name": filename,
                "path": file_path,
                "document_type": doc_type,
                "status": "downloaded_from_sam",
                "text": text[:1000] if text else "",  # Preview
                "page_count": doc_info.get('page_count', 0)
            })
        
        logger.info(f"[SAM.gov] Downloaded {len(result)} document(s)")
        return result
        
    except Exception as e:
        logger.error(f"[ERROR] SAM.gov download error: {e}", exc_info=True)
        return []

def analyze_opportunity(
    base_dir: str,
    opportunity_code: str,
    documents: Optional[List[Dict[str, str]]] = None,
    notice_id: Optional[str] = None,
    opportunity_id: Optional[str] = None,
    form_data: Optional[Dict[str, Any]] = None,
    download_from_sam_gov: bool = False
) -> Dict[str, Any]:
    """
    Fırsat analizini çalıştır - Ana orkestrasyon fonksiyonu
    
    Args:
        base_dir: Temel klasör (örn: ".")
        opportunity_code: Fırsat kodu (örn: "140D0424Q0292")
        documents: Manuel döküman listesi [{"url": "...", "name": "..."}]
        notice_id: SAM.gov Notice ID (download_from_sam_gov=True ise)
        opportunity_id: SAM.gov Opportunity ID (opsiyonel)
        form_data: Form verileri (evaluation_focus, company_name, vb.)
        download_from_sam_gov: SAM.gov'dan otomatik indir
    
    Returns:
        Analiz sonuçları dict
    """
    start_time = datetime.now()
    
    # 1. Klasörü hazırla
    folder = prepare_opportunity_folder(base_dir, opportunity_code)
    logger.info(f"[Step 1] Folder prepared: {folder}")
    
    # 2. Dökümanları indir
    downloaded_docs = []
    
    # ÖNCE mevcut dosyaları kontrol et (SAM.gov indirme başarısız olsa bile)
    logger.info(f"[Step 2] Checking for existing documents in folder...")
    existing_pdfs = list(folder.glob("*.pdf"))
    existing_txts = list(folder.glob("*.txt"))
    existing_docx = list(folder.glob("*.docx")) + list(folder.glob("*.doc"))
    existing_zips = list(folder.glob("*.zip"))
    existing_excel = list(folder.glob("*.xls")) + list(folder.glob("*.xlsx"))
    # analysis_report.pdf'yi hariç tut (bu analiz sonucu)
    existing_pdfs = [p for p in existing_pdfs if p.name != 'analysis_report.pdf' and p.name != 'sow.pdf']
    existing_docs = existing_pdfs + existing_txts + existing_docx + existing_excel
    
    # ZIP dosyalarını ayıkla
    for zip_file in existing_zips:
        extracted = extract_zip_to_folder(zip_file, folder)
        if extracted:
            logger.info(f"[ZIP] {len(extracted)} dosya ayıklandı: {zip_file.name}")
            existing_docs.extend(extracted)
    
    # Mevcut dosyaları işle
    if existing_docs:
        logger.info(f"[Step 2a] Found {len(existing_docs)} existing document(s) in folder, processing...")
        try:
            from document_processor import DocumentProcessor
            processor = DocumentProcessor()
            for doc_file in existing_docs:
                # Dosyayı işle
                result = processor.process_file_from_path(str(doc_file))
                if result.get('success'):
                    text = result['data'].get('text', '')
                    downloaded_docs.append({
                        "name": doc_file.name,
                        "path": str(doc_file),
                        "document_type": detect_document_type(doc_file.name, text),
                        "status": "existing",
                        "text": text,
                        "page_count": result['data'].get('page_count', 0)
                    })
                    logger.info(f"  ✅ Processed: {doc_file.name} ({len(text)} chars)")
        except ImportError:
            # DocumentProcessor yoksa, sadece metadata ekle
            for doc_file in existing_docs:
                downloaded_docs.append({
                    "name": doc_file.name,
                    "path": str(doc_file),
                    "document_type": detect_document_type(doc_file.name),
                    "status": "existing"
                })
                logger.info(f"  ✅ Added: {doc_file.name}")
    
    # Eğer mevcut dosya yoksa ve SAM.gov indirme aktifse, SAM.gov'dan indir
    if not downloaded_docs and download_from_sam_gov and (notice_id or opportunity_id):
        logger.info(f"[Step 2b] No existing documents found, downloading from SAM.gov...")
        # Önce notice_id ile dene (eğer varsa)
        if notice_id:
            logger.info(f"[Step 2b-1] Trying with Notice ID: {notice_id}")
            downloaded_docs = download_from_sam(
                folder=folder,
                notice_id=notice_id,
                opportunity_id=opportunity_id
            )
        
        # Notice ID ile başarısız olduysa ve opportunity_id farklıysa, opportunity_id ile dene
        if not downloaded_docs and opportunity_id and opportunity_id != notice_id:
            logger.info(f"[Step 2b-2] Notice ID failed, trying with Opportunity ID: {opportunity_id}")
            downloaded_docs = download_from_sam(
                folder=folder,
                notice_id=opportunity_id,  # opportunity_id'yi notice_id olarak kullan
                opportunity_id=opportunity_id
            )
    elif documents:
        logger.info(f"[Step 2] Downloading {len(documents)} document(s)...")
        downloaded_docs = download_documents(folder, documents)
    else:
        # Klasörde mevcut dosyaları kullan (PDF, TXT, DOCX, ZIP, XLS, XLSX)
        existing_pdfs = list(folder.glob("*.pdf"))
        existing_txts = list(folder.glob("*.txt"))
        existing_docx = list(folder.glob("*.docx")) + list(folder.glob("*.doc"))
        existing_zips = list(folder.glob("*.zip"))
        existing_excel = list(folder.glob("*.xls")) + list(folder.glob("*.xlsx"))
        # analysis_report.pdf'yi hariç tut (bu analiz sonucu)
        existing_pdfs = [p for p in existing_pdfs if p.name != 'analysis_report.pdf']
        existing_docs = existing_pdfs + existing_txts + existing_docx + existing_excel
        
        # ZIP dosyalarını ayıkla
        for zip_file in existing_zips:
            extracted = extract_zip_to_folder(zip_file, folder)
            if extracted:
                logger.info(f"[ZIP] {len(extracted)} dosya ayıklandı: {zip_file.name}")
                existing_docs.extend(extracted)
        
        if existing_docs:
            logger.info(f"[Step 2] Using {len(existing_docs)} existing document(s)...")
            try:
                from document_processor import DocumentProcessor
                processor = DocumentProcessor()
                for doc_file in existing_docs:
                    # Dosyayı işle
                    result = processor.process_file_from_path(str(doc_file))
                    if result.get('success'):
                        text = result['data'].get('text', '')
                        downloaded_docs.append({
                            "name": doc_file.name,
                            "path": str(doc_file),
                            "document_type": detect_document_type(doc_file.name, text),
                            "status": "existing",
                            "text": text,
                            "page_count": result['data'].get('page_count', 0)
                        })
                        logger.info(f"  ✅ Processed: {doc_file.name} ({len(text)} chars)")
            except ImportError:
                # DocumentProcessor yoksa, sadece metadata ekle
                for doc_file in existing_docs:
                    downloaded_docs.append({
                        "name": doc_file.name,
                        "path": str(doc_file),
                        "document_type": detect_document_type(doc_file.name),
                        "status": "existing"
                    })
                    logger.info(f"  ✅ Added: {doc_file.name}")
        else:
            logger.warning(f"[WARNING] No documents found in {folder}")
    
    if not downloaded_docs:
        error_msg = f"No documents available for analysis in {folder}"
        if notice_id or opportunity_id:
            error_msg += f"\n\nTried downloading from SAM.gov with:"
            if notice_id:
                error_msg += f"\n  - Notice ID: {notice_id}"
            if opportunity_id and opportunity_id != notice_id:
                error_msg += f"\n  - Opportunity ID: {opportunity_id}"
            error_msg += f"\n\nPossible reasons:"
            error_msg += f"\n  1. SAM.gov API quota limit exceeded (try again tomorrow)"
            error_msg += f"\n  2. No documents attached to this opportunity"
            error_msg += f"\n  3. Documents are not publicly available"
            error_msg += f"\n\nSolution:"
            error_msg += f"\n  - Manually download PDFs from SAM.gov and place them in: {folder}"
            error_msg += f"\n  - Or visit: https://sam.gov/opp/{opportunity_id or notice_id}/view"
        else:
            error_msg += f"\n\n💡 İpucu: SAM.gov API quota limiti aşılmış olabilir. Yarın tekrar deneyin veya manuel olarak PDF'leri klasöre ekleyin."
        
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    logger.info(f"[OK] {len(downloaded_docs)} document(s) ready for analysis")
    
    # 3. Pipeline'ı çalıştır
    logger.info(f"[Step 3] Running MergenLite analysis pipeline...")
    
    # Eğer SAM.gov'dan başarıyla indirildiyse, notice_id/opportunity_id'yi de ver
    # Ama eğer mevcut dosyalar kullanılıyorsa, sadece folder_path kullan
    # (Bu şekilde pipeline tekrar SAM.gov'dan indirmeye çalışmaz)
    use_sam_download = download_from_sam_gov and downloaded_docs and any(
        doc.get('status') != 'existing' for doc in downloaded_docs
    )
    
    result = run_mergen_opportunity_analysis(
        folder_path=str(folder),  # Her zaman folder_path kullan (mevcut dosyalar için)
        notice_id=notice_id if use_sam_download else None,  # Sadece gerçekten indirildiyse
        opportunity_id=opportunity_id if use_sam_download else None,
        form_data=form_data,
        output_dir=str(folder)
    )
    
    # 4. Metadata ekle
    duration = (datetime.now() - start_time).total_seconds()
    
    # PDF path'i kontrol et
    pdf_path = folder / "analysis_report.pdf"
    
    result['metadata'] = {
        'opportunity_code': opportunity_code,
        'folder': str(folder),
        'documents_count': len(downloaded_docs),
        'document_types': [doc.get('document_type', 'unknown') for doc in downloaded_docs],
        'analysis_duration_seconds': duration,
        'analysis_timestamp': datetime.now().isoformat(),
        'report_json_path': str(folder / 'report.json'),
        'summary_md_path': str(folder / 'summary.md'),
        'report_pdf_path': str(pdf_path) if pdf_path.exists() else None
    }
    
    logger.info(f"[OK] Analysis completed in {duration:.2f}s")
    logger.info(f"[Report] {folder / 'report.json'}")
    logger.info(f"[Summary] {folder / 'summary.md'}")
    if pdf_path.exists():
        logger.info(f"[PDF] {pdf_path}")
    
    # 5. Veritabanına kaydet
    try:
        from backend_utils import get_db_session
        from mergenlite_models import AIAnalysisResult
        import json
        
        db = get_db_session()
        if db:
            try:
                # Report JSON'dan skor hesapla
                report_json_path = folder / 'report.json'
                overall_score = 0
                confidence = 0.5
                
                if report_json_path.exists():
                    try:
                        with open(report_json_path, 'r', encoding='utf-8') as f:
                            report_data = json.load(f)
                            
                        # Skor hesapla
                        fit_assessment = report_data.get('fit_assessment', {})
                        if fit_assessment and fit_assessment.get('overall_score'):
                            overall_score = float(fit_assessment.get('overall_score', 0))
                        elif report_data.get('compliance', {}).get('score'):
                            overall_score = float(report_data.get('compliance', {}).get('score', 0))
                        
                        confidence = overall_score / 100.0 if overall_score > 0 else 0.5
                    except Exception as json_error:
                        logger.warning(f"Report JSON okuma hatası: {json_error}")
                
                # AIAnalysisResult kaydet
                ai_result = AIAnalysisResult(
                    opportunity_id=notice_id or opportunity_id or opportunity_code,
                    analysis_type='FULL_ANALYSIS',
                    result=result,  # Full result dict
                    confidence=confidence,
                    timestamp=datetime.now(),
                    agent_name='MergenLite Opportunity Runner'
                )
                
                db.add(ai_result)
                db.commit()
                
                logger.info(f"✅ Analiz sonucu veritabanına kaydedildi: {ai_result.id} (opportunity_id: {ai_result.opportunity_id})")
            except Exception as db_error:
                logger.error(f"❌ Veritabanı kayıt hatası: {db_error}", exc_info=True)
                if db:
                    db.rollback()
            finally:
                db.close()
    except ImportError:
        logger.warning("Backend utils veya models import edilemedi, veritabanı kaydı atlandı")
    except Exception as save_error:
        logger.error(f"Veritabanı kayıt hatası: {save_error}", exc_info=True)
    
    return result

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Test örneği
    if len(sys.argv) < 2:
        print("Usage: python opportunity_runner.py <opportunity_code> [--notice-id <id>] [--form-data <json>]")
        sys.exit(1)
    
    opportunity_code = sys.argv[1]
    notice_id = None
    form_data = None
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--notice-id' and i + 1 < len(sys.argv):
            notice_id = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--form-data' and i + 1 < len(sys.argv):
            import json
            form_data = json.loads(sys.argv[i + 1])
            i += 2
        else:
            i += 1
    
    try:
        result = analyze_opportunity(
            base_dir=".",
            opportunity_code=opportunity_code,
            notice_id=notice_id,
            form_data=form_data,
            download_from_sam_gov=bool(notice_id)
        )
        print("\n[OK] Analysis completed successfully!")
        print(f"Report: {result['metadata']['folder']}/report.json")
        print(f"Summary: {result['metadata']['folder']}/summary.md")
    except Exception as e:
        logger.error(f"[ERROR] Analysis failed: {e}", exc_info=True)
        sys.exit(1)


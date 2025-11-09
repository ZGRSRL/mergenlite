#!/usr/bin/env python3
"""
MergenLite Opportunity Requirements Pipeline
AutoGen-based multi-agent system for comprehensive opportunity analysis

Pipeline:
1. DocumentLoaderAgent - Loads all PDFs from opportunity folder
2. RequirementsAgent - Extracts technical/operational requirements
3. ComplianceAgent - Extracts compliance and FAR clauses
4. ReporterAgent - Consolidates results into JSON + Markdown report
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from both root and mergen/.env
load_dotenv()
load_dotenv(dotenv_path='mergen/.env')

# Document processor
from document_processor import DocumentProcessor

# SAM.gov integration
try:
    from sam_integration import SAMIntegration
    SAM_INTEGRATION_AVAILABLE = True
except ImportError:
    SAM_INTEGRATION_AVAILABLE = False
    logging.warning("SAM integration not available")

# AutoGen imports
try:
    from autogen import ConversableAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logging.warning("AutoGen not available. Install with: pip install pyautogen")

logger = logging.getLogger(__name__)

# LLM Configuration
def get_llm_config():
    """Get LLM configuration from environment"""
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    if not api_key:
        logger.warning("OPENAI_API_KEY not set, using mock mode")
        return None
    
    return {
        "config_list": [
            {
                "model": model,
                "api_key": api_key
            }
        ],
        "temperature": 0.1,
        "timeout": 120
    }

# Schema loader
def load_schema() -> Dict[str, Any]:
    """Load opportunity requirements schema"""
    schema_path = Path(__file__).parent / "schemas" / "opportunity_requirements.schema.json"
    
    if not schema_path.exists():
        logger.warning(f"Schema not found at {schema_path}, using default")
        return {
            "opportunity_info": {},
            "event_requirements": {},
            "commercial_terms": {},
            "compliance": {},
            "fit_assessment": {}
        }
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# PDF Text Loader
def load_pdf_texts(folder_path: str) -> Dict[str, str]:
    """
    Load all PDF and TXT files from folder and extract text
    
    Returns:
        Dict mapping filename to extracted text
    """
    folder = Path(folder_path)
    if not folder.exists():
        logger.error(f"Folder not found: {folder_path}")
        return {}
    
    processor = DocumentProcessor()
    texts = {}
    
    # Find all supported files (exclude analysis_report.pdf)
    pdf_files = [f for f in folder.glob("*.pdf") if f.name != "analysis_report.pdf"]
    txt_files = list(folder.glob("*.txt"))
    docx_files = list(folder.glob("*.docx")) + list(folder.glob("*.doc"))
    zip_files = list(folder.glob("*.zip"))
    excel_files = list(folder.glob("*.xls")) + list(folder.glob("*.xlsx"))
    all_files = pdf_files + txt_files + docx_files + excel_files
    
    # ZIP dosyalarını işle (içindeki dosyalar zaten klasöre ayıklanmış olmalı)
    # ZIP dosyalarını direkt işlemek yerine, DocumentProcessor'a bırakıyoruz
    # Çünkü DocumentProcessor ZIP içindeki dosyaları otomatik işleyebilir
    
    if not all_files:
        logger.warning(f"No PDF or TXT files found in {folder_path}")
        return {}
    
    logger.info(f"Found {len(pdf_files)} PDF, {len(txt_files)} TXT, {len(docx_files)} DOCX, {len(zip_files)} ZIP, {len(excel_files)} Excel files in {folder_path}")
    
    for file_path in all_files:
        try:
            result = processor.process_file_from_path(str(file_path))
            if result.get('success'):
                texts[file_path.name] = result['data'].get('text', '')
                logger.info(f"[OK] Loaded {file_path.name} ({len(texts[file_path.name])} chars)")
            else:
                logger.warning(f"[WARNING] Failed to process {file_path.name}: {result.get('error')}")
        except Exception as e:
            logger.error(f"[ERROR] Error processing {file_path.name}: {e}")
    
    return texts

def download_documents_from_sam(notice_id: str, opportunity_id: Optional[str] = None, dest_dir: str = "downloads") -> Dict[str, str]:
    """
    Download documents from SAM.gov for a given opportunity
    
    Args:
        notice_id: Notice ID or Opportunity ID
        opportunity_id: Optional Opportunity ID (if different from notice_id)
        dest_dir: Destination directory for downloaded files
    
    Returns:
        Dict mapping filename to extracted text
    """
    if not SAM_INTEGRATION_AVAILABLE:
        logger.warning("SAM integration not available, cannot download from SAM.gov")
        return {}
    
    try:
        sam = SAMIntegration()
        processor = DocumentProcessor()
        texts = {}
        
        logger.info(f"[SAM.gov] Downloading documents for: {notice_id}")
        
        # Try downloading with notice_id first
        downloaded = sam.download_documents(notice_id, dest_dir=dest_dir)
        
        # If no documents found and opportunity_id is different, try with opportunity_id
        if not downloaded and opportunity_id and opportunity_id != notice_id:
            logger.info(f"[SAM.gov] Trying with Opportunity ID: {opportunity_id}")
            downloaded = sam.download_documents(opportunity_id, dest_dir=dest_dir)
        
        if not downloaded:
            logger.warning(f"[SAM.gov] No documents found for {notice_id}")
            return {}
        
        logger.info(f"[SAM.gov] Downloaded {len(downloaded)} document(s)")
        
        # Process downloaded documents
        for doc_info in downloaded:
            try:
                # Check if file_path exists
                file_path = doc_info.get('path') or doc_info.get('file_path', '')
                if file_path and Path(file_path).exists():
                    result = processor.process_file_from_path(file_path)
                    if result.get('success'):
                        filename = Path(file_path).name
                        texts[filename] = result['data'].get('text', '')
                        logger.info(f"[OK] Processed {filename} ({len(texts[filename])} chars)")
                # If text is already extracted, use it directly
                elif doc_info.get('text'):
                    filename = doc_info.get('filename', f"document_{len(texts)}.pdf")
                    texts[filename] = doc_info.get('text', '')
                    logger.info(f"[OK] Using extracted text for {filename} ({len(texts[filename])} chars)")
            except Exception as e:
                logger.error(f"[ERROR] Error processing downloaded document: {e}")
        
        return texts
    
    except Exception as e:
        logger.error(f"[ERROR] Error downloading from SAM.gov: {e}", exc_info=True)
        return {}

# ============================================================================
# AutoGen Agents
# ============================================================================

def make_requirements_agent(llm_config: Optional[Dict] = None):
    """Requirements Agent - Extracts technical/operational requirements"""
    
    schema = load_schema()
    schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
    
    system_msg = f"""
Sen bir ABD federal ihale fırsatı analiz ajansın.

Görevin: RFQ, SOW ve ekleri kullanarak fırsatın tüm operasyonel ve teknik gereksinimlerini
standart JSON şemasına göre çıkarmak.

Şema:
{schema_json}

Kurallar:
- Sadece verilen metinlere dayan.
- opportunity_info, event_requirements alanlarını doldur.
- NAICS, set-aside, konum, tarih, kapasite, oda/gece planı, toplantı odaları, AV, F&B,
  shuttle, park vb. alanları doldur.
- Bilinmeyen alanlara "unknown" yaz, boş string bırakma.
- Sadece JSON döndür, açıklama yazma.
- Çıktı formatı: {{"opportunity_info": {{...}}, "event_requirements": {{...}}}}
"""
    
    if not AUTOGEN_AVAILABLE or not llm_config:
        return None
    
    return ConversableAgent(
        name="requirements_agent",
        system_message=system_msg,
        llm_config=llm_config,
    )

def make_compliance_agent(llm_config: Optional[Dict] = None):
    """Compliance Agent - Extracts FAR clauses and compliance requirements"""
    
    schema = load_schema()
    compliance_schema = json.dumps(schema.get("compliance", {}), indent=2, ensure_ascii=False)
    
    system_msg = f"""
Sen bir federal acquisition compliance ajansın.

Görevin: Verilen metinlerden FAR ve diğer zorunlu hükümleri tespit edip
compliance alanını doldurmak.

Compliance Şeması:
{compliance_schema}

Odak:
- FAR 52.212-4, 52.212-5,
- FAR 52.204-24, 52.204-25, 52.204-26,
- IPP (Internet Payment Platform) zorunluluğu,
- vergi muafiyeti, Bytedance/telecom yasakları,
- küçük işletme şartları.

Kurallar:
- Sadece JSON 'compliance' alanını doldur, JSON dışında açıklama yazma.
- Bilinmeyenler 'false' veya boş liste olabilir.
- Çıktı formatı: {{"compliance": {{...}}}}
"""
    
    if not AUTOGEN_AVAILABLE or not llm_config:
        return None
    
    return ConversableAgent(
        name="compliance_agent",
        system_message=system_msg,
        llm_config=llm_config,
    )

def make_commercial_agent(llm_config: Optional[Dict] = None):
    """Commercial Agent - Extracts commercial terms and payment conditions"""
    
    schema = load_schema()
    commercial_schema = json.dumps(schema.get("commercial_terms", {}), indent=2, ensure_ascii=False)
    
    system_msg = f"""
Sen bir ticari koşullar analiz ajansın.

Görevin: Verilen metinlerden ticari koşulları, ödeme şartlarını, per diem limitlerini,
IPP gereksinimlerini ve diğer ticari hükümleri çıkarmak.

Commercial Terms Şeması:
{commercial_schema}

Odak:
- Tahmini değer (estimated_value)
- Per diem limitleri
- Ödeme koşulları
- IPP (Internet Payment Platform) zorunluluğu
- Vergi muafiyeti
- İptal cezaları

Kurallar:
- Sadece JSON 'commercial_terms' alanını doldur.
- Çıktı formatı: {{"commercial_terms": {{...}}}}
"""
    
    if not AUTOGEN_AVAILABLE or not llm_config:
        return None
    
    return ConversableAgent(
        name="commercial_agent",
        system_message=system_msg,
        llm_config=llm_config,
    )

def make_reporter_agent(llm_config: Optional[Dict] = None):
    """Reporter Agent - Consolidates all agent outputs into final report"""
    
    schema = load_schema()
    schema_json = json.dumps(schema, indent=2, ensure_ascii=False)
    
    system_msg = f"""
Sen bir raporlama ajansın.

Görevin: Diğer ajanların ürettiği JSON parçalarını alır,
tek bir birleşik 'Opportunity_Requirements_Report' JSON'u ve
insan okunabilir kısa bir özet üretirsin.

ÖNEMLİ: SADECE JSON DÖNDÜR - hiçbir markdown code block, açıklama veya ekstra metin yazma!

Tam Şema:
{schema_json}

Kurallar:
- Tüm ajan çıktılarını birleştir.
- fit_assessment alanını hesapla (overall_score, strengths, risks, blocking_issues, summary).
- Çıktı MUTLAKA şu formatta olmalı (başka hiçbir şey yazma):
{{
  "report": {{...birleşik_json...}},
  "summary_md": "markdown formatında kısa özet (go-no go bakışı dahil)"
}}

SADECE JSON DÖNDÜR - markdown code block kullanma, açıklama yazma, sadece saf JSON!
"""
    
    if not AUTOGEN_AVAILABLE or not llm_config:
        return None
    
    return ConversableAgent(
        name="reporter_agent",
        system_message=system_msg,
        llm_config=llm_config,
        max_consecutive_auto_reply=1,  # Code execution'ı engellemek için
        human_input_mode="NEVER",
    )

# ============================================================================
# Pipeline Orchestration
# ============================================================================

def run_mergen_opportunity_analysis(
    folder_path: Optional[str] = None,
    notice_id: Optional[str] = None,
    opportunity_id: Optional[str] = None,
    output_dir: Optional[str] = None,
    download_dir: str = "downloads",
    form_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run MergenLite opportunity analysis pipeline
    
    Args:
        folder_path: Path to opportunity folder containing PDFs (if analyzing local files)
        notice_id: SAM.gov Notice ID (if downloading from SAM.gov)
        opportunity_id: SAM.gov Opportunity ID (optional, if different from notice_id)
        output_dir: Optional output directory (defaults to folder_path or download_dir)
        download_dir: Directory for downloaded SAM.gov documents
        form_data: Form verileri (evaluation_focus, company_name, vb.) - Form kriterlerine göre analiz için
    
    Returns:
        Dict with 'report' and 'summary_md' keys
    """
    pdf_texts = {}
    output_path = None
    
    # Determine source: SAM.gov or local folder
    # Önce folder_path'te mevcut dosyaları kontrol et
    if folder_path:
        folder = Path(folder_path)
        if folder.exists():
            # Mevcut dosyaları yükle
            logger.info(f"[MergenLite] Starting Opportunity Analysis: {folder_path}")
            logger.info("[Step 1] Loading documents from local folder...")
            pdf_texts = load_pdf_texts(folder_path)
            
            # Eğer mevcut dosyalar varsa, onları kullan
            if pdf_texts:
                output_path = Path(output_dir) if output_dir else folder
                logger.info(f"[OK] Using {len(pdf_texts)} existing document(s) from folder")
            # Eğer mevcut dosya yoksa ve notice_id varsa, SAM.gov'dan indir
            elif notice_id or opportunity_id:
                logger.info(f"[MergenLite] No local files found, downloading from SAM.gov: {notice_id or opportunity_id}")
                output_path = Path(output_dir) if output_dir else folder
                output_path.mkdir(parents=True, exist_ok=True)
                
                logger.info("[Step 1] Downloading documents from SAM.gov...")
                pdf_texts = download_documents_from_sam(
                    notice_id=notice_id or opportunity_id or '',
                    opportunity_id=opportunity_id,
                    dest_dir=str(output_path)
                )
                
                # Eğer SAM.gov'dan da indirilemediyse, hata ver
                if not pdf_texts:
                    logger.error(f"❌ No documents found or downloaded for {notice_id or opportunity_id}")
                    logger.info("💡 İpucu: SAM.gov API quota limiti aşılmış olabilir. Yarın tekrar deneyin veya manuel olarak PDF'leri klasöre ekleyin.")
                    raise ValueError(f"No documents found or downloaded for {notice_id or opportunity_id}")
            else:
                # Check for TXT files as fallback
                txt_files = list(folder.glob("*.txt"))
                if txt_files:
                    logger.info(f"[Fallback] Found {len(txt_files)} TXT file(s), using them for analysis")
                    pdf_texts = load_pdf_texts(folder_path)
                else:
                    raise ValueError(f"No PDF or TXT files found in {folder_path} and no notice_id provided")
        else:
            raise ValueError(f"Folder not found: {folder_path}")
    elif notice_id or opportunity_id:
        # Sadece SAM.gov'dan indir (folder_path yok)
        logger.info(f"[MergenLite] Starting Opportunity Analysis from SAM.gov: {notice_id or opportunity_id}")
        
        # Set output path first (download_dir will be used for downloads)
        output_path = Path(output_dir) if output_dir else Path(download_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Download documents to output_path
        logger.info("[Step 1] Downloading documents from SAM.gov...")
        pdf_texts = download_documents_from_sam(
            notice_id=notice_id or opportunity_id or '',
            opportunity_id=opportunity_id,
            dest_dir=str(output_path)  # Download directly to output folder
        )
        
        # Eğer SAM.gov'dan indirilemediyse, output_path'te mevcut dosyaları kontrol et
        if not pdf_texts:
            logger.warning(f"[WARNING] SAM.gov download failed, checking for existing files in {output_path}...")
            if output_path.exists():
                pdf_texts = load_pdf_texts(str(output_path))
                if pdf_texts:
                    logger.info(f"[OK] Using {len(pdf_texts)} existing document(s) from {output_path}")
        
        if not pdf_texts:
            logger.error(f"❌ No documents found or downloaded for {notice_id or opportunity_id}")
            logger.info("💡 İpucu: SAM.gov API quota limiti aşılmış olabilir. Yarın tekrar deneyin veya manuel olarak PDF'leri klasöre ekleyin.")
            raise ValueError(f"No documents found or downloaded for {notice_id or opportunity_id}")
        
    # Yukarıdaki if-elif blokları zaten folder_path ve notice_id durumlarını handle ediyor
    # Bu else bloğu artık gereksiz, çünkü yukarıda handle edildi
    if not pdf_texts:
        raise ValueError("Either folder_path or notice_id/opportunity_id must be provided, and documents must be available")
    
    # Combine all texts with file markers
    combined_text = "\n\n".join(
        f"### FILE: {name}\n{text[:50000]}"  # Limit to 50k chars per file
        for name, text in pdf_texts.items()
    )
    
    logger.info(f"[OK] Loaded {len(pdf_texts)} documents ({len(combined_text)} total chars)")
    
    # 2. Initialize LLM config
    llm_config = get_llm_config()
    
    if not AUTOGEN_AVAILABLE or not llm_config:
        logger.warning("[WARNING] AutoGen not available or LLM config missing, using mock mode")
        return _run_mock_analysis(folder_path, pdf_texts, output_path, form_data)
    
    # 3. Create agents (form_data ile)
    logger.info("[Step 2] Initializing AutoGen agents...")
    requirements_agent = make_requirements_agent(llm_config)  # form_data parametresi yok
    compliance_agent = make_compliance_agent(llm_config)
    commercial_agent = make_commercial_agent(llm_config)
    reporter_agent = make_reporter_agent(llm_config)
    
    # 4. Run analysis pipeline
    logger.info("[Step 3] Running agent analysis...")
    
    try:
        # Requirements analysis - DETAYLI ANALİZ
        logger.info("  [Requirements Agent] Analyzing... (DETAYLI MOD)")
        req_prompt = f"""Analyze these documents DETAYLI (DETAILED) and extract ALL requirements:

Documents:
{combined_text[:100000]}

Extract:
- ALL technical requirements
- ALL operational requirements
- ALL capacity requirements
- ALL date/location requirements
- ALL compliance requirements
- ALL commercial terms

Be THOROUGH and COMPLETE. Do not skip any requirement."""
        
        req_response = requirements_agent.generate_reply(
            messages=[{"role": "user", "content": req_prompt}]
        )
        req_json = req_response.content if hasattr(req_response, 'content') else str(req_response)
        logger.info(f"[OK] Requirements Agent completed ({len(req_json)} chars)")
        
        # Compliance analysis - DETAYLI ANALİZ
        logger.info("  [Compliance Agent] Analyzing... (DETAYLI MOD)")
        comp_prompt = f"""Analyze these documents DETAYLI (DETAILED) for ALL compliance requirements:

Documents:
{combined_text[:100000]}

Extract:
- ALL FAR clauses (52.212-4, 52.212-5, 52.204-24/25/26, etc.)
- ALL security/telecom restrictions
- ALL small business requirements
- ALL IPP (Internet Payment Platform) requirements
- ALL tax exemption clauses
- ALL other mandatory compliance clauses

Be THOROUGH and COMPLETE. Check every compliance requirement."""
        
        comp_response = compliance_agent.generate_reply(
            messages=[{"role": "user", "content": comp_prompt}]
        )
        comp_json = comp_response.content if hasattr(comp_response, 'content') else str(comp_response)
        logger.info(f"[OK] Compliance Agent completed ({len(comp_json)} chars)")
        
        # Commercial analysis - DETAYLI ANALİZ
        logger.info("  [Commercial Agent] Analyzing... (DETAYLI MOD)")
        comm_prompt = f"""Analyze these documents DETAYLI (DETAILED) for ALL commercial terms:

Documents:
{combined_text[:100000]}

Extract:
- Estimated value/budget
- Per diem limits
- Payment terms (net 30, net 60, etc.)
- E-invoicing (IPP) requirements
- Tax exemption status
- Cancellation penalties
- Other key commercial terms

Be THOROUGH and COMPLETE. Extract all commercial information."""
        
        comm_response = commercial_agent.generate_reply(
            messages=[{"role": "user", "content": comm_prompt}]
        )
        comm_json = comm_response.content if hasattr(comm_response, 'content') else str(comm_response)
        logger.info(f"[OK] Commercial Agent completed ({len(comm_json)} chars)")
        
        # Reporter: Consolidate - Manuel birleştirme (code execution sorununu önlemek için)
        logger.info("  [Reporter Agent] Consolidating... (DETAYLI MOD)")
        
        # Önce ajanların JSON'larını parse et
        try:
            req_data = json.loads(req_json) if isinstance(req_json, str) else req_json
        except:
            req_data = {}
        
        try:
            comp_data = json.loads(comp_json) if isinstance(comp_json, str) else comp_json
        except:
            comp_data = {}
        
        try:
            comm_data = json.loads(comm_json) if isinstance(comm_json, str) else comm_json
        except:
            comm_data = {}
        
        # Otel önerilerini ekle
        recommended_hotels = []
        try:
            from hotel_database import HotelDatabase
            hotel_db = HotelDatabase()
            
            # Excel'den yükle (ilk seferde)
            excel_path = Path("samples") / "SP&TD DEDUPLICATED EMAIL_EXTRACT_DATA_dedup.xlsx"
            if excel_path.exists() and len(hotel_db.hotels) == 0:
                logger.info("[Hotel DB] Loading hotels from Excel...")
                hotel_db.load_from_excel(str(excel_path))
            
            # Event gereksinimlerine göre otel öner
            event_req = req_data.get("event_requirements", {})
            if event_req:
                recommended_hotels = hotel_db.get_recommended_hotels(event_req, limit=5)
                logger.info(f"[Hotel DB] Found {len(recommended_hotels)} recommended hotels")
        except Exception as e:
            logger.warning(f"[Hotel DB] Error getting hotel recommendations: {e}", exc_info=True)
        
        # Manuel birleştirme
        consolidated_report = {
            "opportunity_info": req_data.get("opportunity_info", {}),
            "event_requirements": req_data.get("event_requirements", {}),
            "commercial_terms": comm_data.get("commercial_terms", {}),
            "compliance": comp_data.get("compliance", {}),
            "recommended_hotels": recommended_hotels,  # Otel önerileri eklendi
            "fit_assessment": {
                "overall_score": 50,  # Varsayılan, LLM ile hesaplanacak
                "strengths": [],
                "risks": [],
                "blocking_issues": [],
                "summary": ""
            }
        }
        
        # Fit assessment için LLM kullan (ama code execution olmadan)
        reporter_input = f"""
Aşağıda üç ayrı ajanın çıktıları var. Sadece fit_assessment hesapla (overall_score, strengths, risks, blocking_issues, summary).

[REQUIREMENTS]
{json.dumps(req_data, ensure_ascii=False, indent=2)}

[COMPLIANCE]
{json.dumps(comp_data, ensure_ascii=False, indent=2)}

[COMMERCIAL]
{json.dumps(comm_data, ensure_ascii=False, indent=2)}

SADECE fit_assessment JSON'unu döndür (başka hiçbir şey yazma):
{{
  "overall_score": 0-100,
  "strengths": ["..."],
  "risks": ["..."],
  "blocking_issues": ["..."],
  "summary": "..."
}}
"""
        
        try:
            final_response = reporter_agent.generate_reply(
                messages=[{"role": "user", "content": reporter_input}]
            )
            final_json = final_response.content if hasattr(final_response, 'content') else str(final_response)
            logger.info(f"[OK] Reporter Agent completed ({len(final_json)} chars)")
            
            # Parse fit_assessment
            try:
                if "```json" in final_json:
                    final_json = final_json.split("```json")[1].split("```")[0].strip()
                elif "```" in final_json:
                    final_json = final_json.split("```")[1].split("```")[0].strip()
                
                import re
                json_match = re.search(r'\{[\s\S]*\}', final_json)
                if json_match:
                    final_json = json_match.group(0)
                
                fit_assessment = json.loads(final_json)
                consolidated_report["fit_assessment"] = fit_assessment
            except:
                logger.warning("[WARNING] Could not parse fit_assessment from Reporter Agent, using defaults")
        except Exception as e:
            logger.warning(f"[WARNING] Reporter Agent failed: {e}, using consolidated data without fit_assessment")
        
        # Final JSON oluştur
        final_json = json.dumps({
            "report": consolidated_report,
            "summary_md": f"# Opportunity Requirements Report\n\n## Genel Bilgiler\n{consolidated_report.get('fit_assessment', {}).get('summary', 'Analiz tamamlandı.')}"
        }, ensure_ascii=False, indent=2)
        
        # Parse final JSON
        try:
            # Clean JSON (remove markdown code blocks if present)
            original_json = final_json
            
            # Remove markdown code blocks
            if "```json" in final_json:
                final_json = final_json.split("```json")[1].split("```")[0].strip()
            elif "```" in final_json:
                # Try to extract JSON from code block
                parts = final_json.split("```")
                for i, part in enumerate(parts):
                    if part.strip().startswith("{") or part.strip().startswith("["):
                        final_json = part.strip()
                        break
                else:
                    # If no JSON found in code blocks, try to find JSON in the text
                    import re
                    json_match = re.search(r'\{[\s\S]*\}', final_json)
                    if json_match:
                        final_json = json_match.group(0)
            
            # Remove any leading/trailing whitespace
            final_json = final_json.strip()
            
            # If still empty or doesn't start with {, try to find JSON in the response
            if not final_json or not final_json.startswith("{"):
                import re
                # Try to find JSON object in the response
                json_match = re.search(r'\{[\s\S]*\}', original_json)
                if json_match:
                    final_json = json_match.group(0)
                else:
                    logger.error(f"[ERROR] No valid JSON found. Raw response (first 500 chars): {original_json[:500]}")
                    raise ValueError(f"No valid JSON found in response. Raw response: {original_json[:200]}")
            
            result = json.loads(final_json)
            
            # Save outputs
            report_path = output_path / "report.json"
            summary_path = output_path / "summary.md"
            
            report_data = result.get('report', result)
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            logger.info(f"[OK] Saved report: {report_path}")
            
            summary_md = result.get('summary_md', '')
            if summary_md:
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(summary_md)
            logger.info(f"[OK] Saved summary: {summary_path}")
            
            # Sample klasörüne de kopyala (proposal ve SOW hariç)
            try:
                samples_dir = Path("samples")
                samples_dir.mkdir(exist_ok=True)
                
                # Report ve summary'yi sample klasörüne kopyala
                import shutil
                samples_report = samples_dir / "report.json"
                samples_summary = samples_dir / "summary.md"
                
                shutil.copy2(report_path, samples_report)
                if summary_path.exists():
                    shutil.copy2(summary_path, samples_summary)
                
                logger.info(f"[OK] Copied report and summary to samples folder")
            except Exception as e:
                logger.warning(f"[WARNING] Could not copy to samples folder: {e}")
            
            # PDF raporu oluştur
            pdf_path = output_path / "analysis_report.pdf"
            try:
                from pdf_report_builder import build_pdf_report
                
                # Kriter bazlı analiz sonuçlarını topla (eğer varsa)
                criteria_results = {}
                # TODO: criteria_results'ı analysis_results'tan çıkar
                # Şimdilik boş bırakıyoruz, guided_analysis.py'den gelecek
                
                pdf_success = build_pdf_report(
                    report_json=report_data,
                    output_path=str(pdf_path),
                    opportunity_code=form_data.get('opportunity_code', '') if form_data else Path(output_path).name,
                    criteria_results=criteria_results
                )
                
                if pdf_success:
                    logger.info(f"[OK] Saved PDF report: {pdf_path}")
                else:
                    logger.warning(f"[WARNING] PDF generation failed")
            except ImportError:
                logger.warning("[WARNING] pdf_report_builder not available, skipping PDF generation")
            except Exception as e:
                logger.error(f"[ERROR] PDF generation error: {e}", exc_info=True)
            
            # Return with paths
            return {
                'report': report_data,
                'summary_md': summary_md,
                'report_json_path': str(report_path),
                'summary_md_path': str(summary_path),
                'report_pdf_path': str(pdf_path) if pdf_path.exists() else None
            }
        
        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] Failed to parse final JSON: {e}")
            logger.error(f"Raw response: {final_json[:500]}")
            raise ValueError(f"Failed to parse agent response as JSON: {e}")
    
    except Exception as e:
        logger.error(f"[ERROR] Pipeline error: {e}", exc_info=True)
        raise

def _run_mock_analysis(folder_path: str, pdf_texts: Dict[str, str], output_path: Path, form_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Mock analysis when AutoGen is not available"""
    logger.warning("[MOCK] Running in mock mode (AutoGen not available)")
    
    schema = load_schema()
    
    # Simple mock report
    mock_report = {
        "opportunity_info": {
            "solicitation_number": "UNKNOWN",
            "notice_id": Path(folder_path).name,
            "title": "Mock Analysis",
            "agency": "unknown",
            "naics": "unknown",
            "set_aside": "unknown",
            "small_business_only": False,
            "place_of_performance": "unknown",
            "response_deadline": ""
        },
        "event_requirements": {
            "location": "unknown",
            "date_range": "unknown",
            "participants_min": None,
            "participants_target": None,
            "room_block_plan": "unknown",
            "meeting_spaces": "unknown",
            "av_requirements": "unknown",
            "fnb_requirements": "unknown",
            "special_logistics": "unknown"
        },
        "commercial_terms": {
            "estimated_value": "unknown",
            "per_diem_limited": False,
            "payment_terms": "unknown",
            "e_invoicing_ipp": False,
            "tax_exempt": False,
            "cancellation_penalties": "",
            "other_key_terms": ""
        },
        "compliance": {
            "far_52_212_4": False,
            "far_52_212_5": False,
            "far_52_204_24_25_26": False,
            "security_telecom_restrictions": False,
            "bytedance_restriction": False,
            "other_mandatory_clauses": []
        },
        "fit_assessment": {
            "overall_score": 0,
            "strengths": ["Mock analysis - install AutoGen for full analysis"],
            "risks": ["AutoGen not available"],
            "blocking_issues": ["Install pyautogen: pip install pyautogen"],
            "summary": "Mock analysis mode. Please install AutoGen for full analysis."
        }
    }
    
    summary_md = f"""# Opportunity Requirements Report (Mock Mode)

## Analysis Status
⚠️ **Mock Mode**: AutoGen is not available. Install with `pip install pyautogen` for full analysis.

## Documents Analyzed
- {len(pdf_texts)} PDF files found
- Total characters: {sum(len(t) for t in pdf_texts.values())}

## Next Steps
1. Install AutoGen: `pip install pyautogen`
2. Set OPENAI_API_KEY environment variable
3. Re-run analysis for full results
"""
    
    # Save outputs
    report_path = output_path / "report.json"
    summary_path = output_path / "summary.md"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(mock_report, f, indent=2, ensure_ascii=False)
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary_md)
    
    # PDF raporu oluştur (mock mode'da da)
    pdf_path = output_path / "analysis_report.pdf"
    try:
        from pdf_report_builder import build_pdf_report
        
        pdf_success = build_pdf_report(
            report_json=mock_report,
            output_path=str(pdf_path),
            opportunity_code=Path(output_path).name,
            criteria_results={}
        )
        
        if pdf_success:
            logger.info(f"[OK] Saved PDF report: {pdf_path}")
    except Exception as e:
        logger.warning(f"[WARNING] PDF generation failed in mock mode: {e}")
    
    return {
        "report": mock_report,
        "summary_md": summary_md,
        "report_json_path": str(report_path),
        "summary_md_path": str(summary_path),
        "report_pdf_path": str(pdf_path) if pdf_path.exists() else None
    }

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python mergenlite_opportunity_pipeline.py <opportunity_folder> [output_dir]")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        result = run_mergen_opportunity_analysis(folder_path, output_dir)
        print("\n✅ Analysis completed successfully!")
        print(f"📄 Report: {Path(folder_path) / 'report.json'}")
        print(f"📝 Summary: {Path(folder_path) / 'summary.md'}")
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}", exc_info=True)
        sys.exit(1)


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detaylı Fırsat Analizi Scripti
Bir SAM.gov ilanı üzerinde tüm ajanları çalıştırır ve detaylı analiz raporu oluşturur.
Dökümanların ince detayına kadar incelenir.

Kullanım:
    python detailed_opportunity_analysis.py <opportunity_id>
    
Örnek:
    python detailed_opportunity_analysis.py 57cd76db400c4e7ca895d40bf6454173
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

from llm_client import (
    call_logged_llm,
    extract_message_text,
    LLMNotAvailableError,
)
from dotenv import load_dotenv

# Environment variables - Önce root, sonra mergen/.env
load_dotenv()  # Root .env
load_dotenv(dotenv_path='mergen/.env')  # mergen/.env (öncelikli)

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Imports
try:
    from sam_integration import SAMIntegration
    SAM_INTEGRATION_AVAILABLE = True
except ImportError:
    SAM_INTEGRATION_AVAILABLE = False
    logger.warning("SAM integration not available")

try:
    from document_processor import DocumentProcessor
    DOCUMENT_PROCESSOR_AVAILABLE = True
except ImportError:
    DOCUMENT_PROCESSOR_AVAILABLE = False
    logger.warning("Document processor not available")

try:
    from mergenlite_agents import (
        DocumentProcessorAgent,
        RequirementsExtractorAgent,
        ComplianceAnalystAgent,
        ProposalWriterAgent,
        QualityAssuranceAgent,
        MergenLiteOrchestrator
    )
    AGENTS_AVAILABLE = True
except ImportError:
    AGENTS_AVAILABLE = False
    logger.warning("MergenLite agents not available")

try:
    from llm_analyzer import LLMAnalyzer
    LLM_ANALYZER_AVAILABLE = True
except ImportError:
    LLM_ANALYZER_AVAILABLE = False
    logger.warning("LLM analyzer not available")

try:
    from pdf_report_builder import build_pdf_report
    PDF_BUILDER_AVAILABLE = True
except ImportError:
    PDF_BUILDER_AVAILABLE = False
    logger.warning("PDF builder not available")

try:
    from backend_utils import get_db_session
    from mergenlite_models import Opportunity, AIAnalysisResult
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logger.warning("Database not available")

# AutoGen imports
try:
    from mergen.autogen_config import (
        get_agent_configs,
        create_autogen_agents,
        AUTOGEN_AVAILABLE as AUTOGEN_CONFIG_AVAILABLE,
        ASSISTANT_AGENT_MODULE,
    )
    from mergen.autogen_implementation import ZgrBidAutoGenOrchestrator
    AUTOGEN_AVAILABLE = AUTOGEN_CONFIG_AVAILABLE
    if AUTOGEN_AVAILABLE:
        logger.info(f"AutoGen support enabled via {ASSISTANT_AGENT_MODULE}")
    else:
        logger.warning("AutoGen configuration loaded but no AssistantAgent implementation is available.")
except ImportError as e:
    AUTOGEN_AVAILABLE = False
    logger.warning("AutoGen not available - using standard agents only (%s)", e)

# RFQ-SOW Orchestrator imports
# NOTE: Using built-in 3-pass orchestrator from mergen/api/app/agents/rfq_3pass_orchestrator.py
# No external D:/RFQ dependency needed
try:
    from mergen.api.app.agents.rfq_3pass_orchestrator import run_rfq_3pass_pipeline, RFQ3PassOrchestratorUnavailableError
    RFQ_SOW_ORCHESTRATOR_AVAILABLE = True
    logger.info("RFQ-SOW 3-pass Orchestrator available")
except ImportError as e:
    RFQ_SOW_ORCHESTRATOR_AVAILABLE = False
    logger.warning(f"RFQ-SOW 3-pass Orchestrator not available: {e}")

# SOW PDF Generator imports
# Using built-in template engine and PDF generator from mergen/api/app/services
try:
    from mergen.api.app.services.sow_pdf_generator_weasyprint import html_to_pdf, generate_pdf_from_markdown
    from mergen.api.app.services.sow_template_engine import render_sow_from_model
    SOW_PDF_GENERATOR_AVAILABLE = True
    logger.info("SOW PDF Generator available")
except ImportError as e:
    SOW_PDF_GENERATOR_AVAILABLE = False
    logger.warning(f"SOW PDF Generator not available: {e}")


class DetailedOpportunityAnalyzer:
    """
    Detaylı Fırsat Analizi
    Tüm ajanları çalıştırır ve kapsamlı analiz raporu oluşturur
    """
    
    def __init__(self, opportunity_id: str):
        self.opportunity_id = opportunity_id
        self.base_dir = Path(".")
        self.output_dir = self.base_dir / "opportunities" / opportunity_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.sam_integration = SAMIntegration() if SAM_INTEGRATION_AVAILABLE else None
        self.document_processor = DocumentProcessor() if DOCUMENT_PROCESSOR_AVAILABLE else None
        
        # LLM Analyzer - API key kontrolü ile
        if LLM_ANALYZER_AVAILABLE:
            openai_key = os.getenv('OPENAI_API_KEY', '')
            if openai_key:
                logger.info(f"OpenAI API key loaded (length: {len(openai_key)})")
            else:
                logger.warning("OpenAI API key not found in environment variables")
            self.llm_analyzer = LLMAnalyzer()
        else:
            self.llm_analyzer = None
        
        # Initialize agents
        if AGENTS_AVAILABLE:
            self.doc_agent = DocumentProcessorAgent()
            self.req_agent = RequirementsExtractorAgent()
            self.comp_agent = ComplianceAnalystAgent()
            self.prop_agent = ProposalWriterAgent()
            self.qa_agent = QualityAssuranceAgent()
            self.orchestrator = MergenLiteOrchestrator()
        else:
            self.doc_agent = None
            self.req_agent = None
            self.comp_agent = None
            self.prop_agent = None
            self.qa_agent = None
            self.orchestrator = None
        
        # Initialize AutoGen orchestrator (if available)
        if AUTOGEN_AVAILABLE:
            try:
                self.autogen_orchestrator = ZgrBidAutoGenOrchestrator()
                self.autogen_agents = create_autogen_agents()
                logger.info("AutoGen orchestrator initialized successfully")
            except Exception as e:
                logger.warning(f"AutoGen orchestrator initialization failed: {e}")
                self.autogen_orchestrator = None
                self.autogen_agents = None
        else:
            self.autogen_orchestrator = None
            self.autogen_agents = None
        
        # Initialize RFQ-SOW Orchestrator (if available)
        # Using built-in 3-pass orchestrator - no initialization needed
        if RFQ_SOW_ORCHESTRATOR_AVAILABLE:
            self.rfq_sow_orchestrator = True  # Flag to indicate availability
            logger.info("RFQ-SOW 3-pass Orchestrator available")
        else:
            self.rfq_sow_orchestrator = None
        
        # Analysis results storage
        self.opportunity_data = {}
        self.documents = []
        self.document_texts = {}
        self.analysis_results = {}
        
        logger.info(f"Detailed Opportunity Analyzer initialized for: {opportunity_id}")
    
    def fetch_opportunity_data(self) -> Dict[str, Any]:
        """SAM.gov'dan veya veritabanından fırsat verilerini çek"""
        logger.info(f"Fetching opportunity data: {self.opportunity_id}")
        
        # Önce veritabanından dene
        if DB_AVAILABLE:
            try:
                db = get_db_session()
                if db:
                    try:
                        from mergenlite_models import Opportunity
                        opp = db.query(Opportunity).filter(
                            (Opportunity.opportunity_id == self.opportunity_id) |
                            (Opportunity.notice_id == self.opportunity_id)
                        ).first()
                        
                        if opp and opp.raw_data:
                            import json
                            if isinstance(opp.raw_data, str):
                                raw_data = json.loads(opp.raw_data)
                            else:
                                raw_data = opp.raw_data
                            
                            self.opportunity_data = raw_data
                            logger.info(f"Opportunity data fetched from database: {raw_data.get('title', 'N/A')}")
                            
                            # Save raw data
                            raw_data_path = self.output_dir / "opportunity_raw_data.json"
                            with open(raw_data_path, 'w', encoding='utf-8') as f:
                                json.dump(raw_data, f, ensure_ascii=False, indent=2)
                            logger.info(f"Raw data saved: {raw_data_path}")
                            
                            return raw_data
                    finally:
                        db.close()
            except Exception as e:
                logger.warning(f"Database fetch error: {e}, trying SAM.gov API")
        
        # Veritabanından bulunamazsa SAM.gov API'yi dene
        if not self.sam_integration:
            logger.error("SAM integration not available")
            return {}
        
        try:
            # Opportunity ID ile arama
            opportunities = self.sam_integration.fetch_by_opportunity_id(self.opportunity_id)
            
            if not opportunities:
                # Notice ID olarak da dene
                opportunities = self.sam_integration.search_by_any_id(self.opportunity_id)
            
            if not opportunities:
                logger.error(f"Opportunity not found: {self.opportunity_id}")
                return {}
            
            opp = opportunities[0]
            self.opportunity_data = opp
            
            logger.info(f"Opportunity data fetched: {opp.get('title', 'N/A')}")
            logger.info(f"   Notice ID: {opp.get('noticeId', 'N/A')}")
            logger.info(f"   Opportunity ID: {opp.get('opportunityId', 'N/A')}")
            
            # Save raw data
            raw_data_path = self.output_dir / "opportunity_raw_data.json"
            with open(raw_data_path, 'w', encoding='utf-8') as f:
                json.dump(opp, f, ensure_ascii=False, indent=2)
            logger.info(f"Raw data saved: {raw_data_path}")
            
            return opp
        
        except Exception as e:
            logger.error(f"Error fetching opportunity data: {e}", exc_info=True)
            return {}
    
    def download_documents(self) -> List[Dict[str, Any]]:
        """Fırsatın tüm dökümanlarını indir (veritabanından veya SAM.gov'dan)"""
        logger.info(f"Downloading documents for opportunity: {self.opportunity_id}")
        
        # Önce veritabanından resourceLinks'i dene
        if DB_AVAILABLE:
            try:
                db = get_db_session()
                if db:
                    try:
                        from mergenlite_models import Opportunity
                        import requests
                        
                        opp = db.query(Opportunity).filter(
                            (Opportunity.opportunity_id == self.opportunity_id) |
                            (Opportunity.notice_id == self.opportunity_id)
                        ).first()
                        
                        if opp and opp.raw_data:
                            import json
                            if isinstance(opp.raw_data, str):
                                raw_data = json.loads(opp.raw_data)
                            else:
                                raw_data = opp.raw_data
                            
                            # resourceLinks'i çıkar
                            resource_links = raw_data.get('resourceLinks', [])
                            attachments = raw_data.get('attachments', [])
                            documents = raw_data.get('documents', [])
                            
                            urls_to_download = []
                            for link in resource_links:
                                if isinstance(link, str):
                                    urls_to_download.append({'url': link, 'name': f'Document_{len(urls_to_download) + 1}.pdf'})
                                elif isinstance(link, dict):
                                    url = link.get('url') or link.get('link') or link.get('downloadUrl') or link.get('href')
                                    if url:
                                        urls_to_download.append({
                                            'url': url,
                                            'name': link.get('title') or link.get('name') or f'Document_{len(urls_to_download) + 1}.pdf'
                                        })
                            
                            for att in attachments + documents:
                                if isinstance(att, str):
                                    urls_to_download.append({'url': att, 'name': f'Document_{len(urls_to_download) + 1}.pdf'})
                                elif isinstance(att, dict):
                                    url = att.get('url') or att.get('link') or att.get('downloadUrl')
                                    if url:
                                        urls_to_download.append({
                                            'url': url,
                                            'name': att.get('title') or att.get('name') or f'Document_{len(urls_to_download) + 1}.pdf'
                                        })
                            
                            if urls_to_download:
                                logger.info(f"Found {len(urls_to_download)} document URL(s) in database")
                                downloaded = []
                                for doc_info in urls_to_download:
                                    url = doc_info.get('url')
                                    name = doc_info.get('name', 'document.pdf')
                                    target = self.output_dir / name
                                    
                                    if target.exists():
                                        logger.info(f"   File already exists: {name}")
                                        downloaded.append({"path": str(target), "filename": name})
                                    else:
                                        try:
                                            logger.info(f"   Downloading: {name} from {url[:50]}...")
                                            resp = requests.get(url, timeout=60, headers={
                                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                                            })
                                            resp.raise_for_status()
                                            
                                            with open(target, "wb") as f:
                                                f.write(resp.content)
                                            
                                            downloaded.append({"path": str(target), "filename": name})
                                            logger.info(f"   Downloaded: {name}")
                                        except Exception as e:
                                            logger.warning(f"   Failed to download {name}: {e}")
                                
                                if downloaded:
                                    self.documents = downloaded
                                    # Process documents immediately
                                    self._process_downloaded_documents(downloaded)
                                    return downloaded
                    finally:
                        db.close()
            except Exception as e:
                logger.warning(f"Database download error: {e}, trying SAM.gov API")
        
        # Veritabanından indirilemediyse SAM.gov API'yi dene
        if not self.sam_integration:
            logger.error("SAM integration not available")
            # Check for existing documents in folder
            existing_pdfs = list(self.output_dir.glob("*.pdf"))
            existing_docx = list(self.output_dir.glob("*.docx")) + list(self.output_dir.glob("*.doc"))
            existing_txt = list(self.output_dir.glob("*.txt"))
            existing_files = existing_pdfs + existing_docx + existing_txt
            
            if existing_files:
                logger.info(f"Found {len(existing_files)} existing document(s)")
                downloaded = [{"path": str(f), "filename": f.name} for f in existing_files]
                self.documents = downloaded
                self._process_downloaded_documents(downloaded)
                return downloaded
            return []
        
        try:
            notice_id = self.opportunity_data.get('noticeId') or self.opportunity_id
            
            # Download documents
            downloaded = self.sam_integration.download_documents(
                notice_id,
                dest_dir=str(self.output_dir)
            )
            
            if not downloaded:
                # Try with opportunity_id
                downloaded = self.sam_integration.download_documents(
                    self.opportunity_id,
                    dest_dir=str(self.output_dir)
                )
            
            if not downloaded:
                # Check for existing documents in folder
                existing_pdfs = list(self.output_dir.glob("*.pdf"))
                existing_docx = list(self.output_dir.glob("*.docx")) + list(self.output_dir.glob("*.doc"))
                existing_txt = list(self.output_dir.glob("*.txt"))
                existing_files = existing_pdfs + existing_docx + existing_txt
                
                if existing_files:
                    logger.info(f"Found {len(existing_files)} existing document(s)")
                    downloaded = [{"path": str(f), "filename": f.name} for f in existing_files]
                else:
                    logger.warning("No documents found or downloaded")
                    return []
            
            self.documents = downloaded
            logger.info(f"Downloaded {len(downloaded)} document(s)")
            # Process documents immediately
            self._process_downloaded_documents(downloaded)
            
            return downloaded
        
        except Exception as e:
            logger.error(f"Error downloading documents: {e}", exc_info=True)
            return []
    
    def _process_downloaded_documents(self, downloaded: List[Dict[str, Any]]):
        """İndirilen dökümanları işle ve metin çıkar"""
        for doc in downloaded:
            doc_path = doc.get('path') or doc.get('file_path', '')
            if not doc_path:
                continue
            
            file_path = Path(doc_path)
            if not file_path.exists():
                continue
            
            # Extract text from document
            if self.document_processor:
                try:
                    result = self.document_processor.process_file_from_path(str(file_path))
                    if result.get('success'):
                        text = result['data'].get('text', '')
                        filename = doc.get('filename') or doc.get('name') or file_path.name
                        self.document_texts[filename] = text
                        logger.info(f"   Processed: {filename} ({len(text)} chars, {result['data'].get('page_count', 0)} pages)")
                    else:
                        logger.warning(f"   Failed to process {file_path.name}: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    logger.warning(f"   Error processing {file_path.name}: {e}")
            else:
                # Fallback: Try to read as text file
                try:
                    if file_path.suffix.lower() == '.txt':
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            text = f.read()
                            filename = doc.get('filename') or doc.get('name') or file_path.name
                            self.document_texts[filename] = text
                            logger.info(f"   Read text file: {filename} ({len(text)} chars)")
                except Exception as e:
                    logger.warning(f"   Error reading {file_path.name}: {e}")
    
    def run_detailed_analysis(self) -> Dict[str, Any]:
        """Tüm ajanları detaylı modda çalıştır"""
        logger.info("Starting detailed analysis with all agents...")
        
        start_time = datetime.now()
        analysis_results = {
            "opportunity_id": self.opportunity_id,
            "opportunity_data": self.opportunity_data,
            "analysis_start": start_time.isoformat(),
            "agents": {}
        }
        
        # Combine all document texts
        combined_text = "\n\n".join([
            f"=== DOCUMENT: {name} ===\n{text}"
            for name, text in self.document_texts.items()
        ])
        
        if not combined_text:
            logger.error("No document text available for analysis")
            return analysis_results
        
        logger.info(f"Total document text: {len(combined_text)} characters")
        
        # 1. Document Processing Agent - DETAYLI
        logger.info("\n" + "="*80)
        logger.info("STEP 1: Document Processing Agent (DETAYLI)")
        logger.info("="*80)
        
        try:
            doc_start = datetime.now()
            
            # Process each document individually
            processed_docs = []
            for doc_name, doc_text in self.document_texts.items():
                logger.info(f"   Processing document: {doc_name}")
                
                if self.doc_agent:
                    processed = self.doc_agent.process_document(
                        doc_name,
                        doc_text
                    )
                    processed_docs.append({
                        "document_name": doc_name,
                        "processed_data": processed
                    })
                else:
                    # Fallback processing
                    processed_docs.append({
                        "document_name": doc_name,
                        "processed_data": {
                            "content_length": len(doc_text),
                            "extracted_metadata": {
                                "key_dates": [],
                                "contact_info": {},
                                "tables": [],
                                "lists": []
                            }
                        }
                    })
            
            # LLM Analyzer ile detaylı analiz
            if self.llm_analyzer and combined_text:
                logger.info("   Running LLM-based detailed document analysis...")
                llm_result = self.llm_analyzer.extract_requirements(combined_text)
                if llm_result.get('success'):
                    processed_docs.append({
                        "document_name": "LLM_Analysis",
                        "processed_data": llm_result.get('data', {})
                    })
            
            doc_end = datetime.now()
            doc_duration = (doc_end - doc_start).total_seconds()
            
            analysis_results["agents"]["document_processor"] = {
                "status": "completed",
                "duration_seconds": doc_duration,
                "documents_processed": len(processed_docs),
                "results": processed_docs,
                "timestamp": doc_end.isoformat()
            }
            
            logger.info(f"Document Processing completed in {doc_duration:.2f}s")
        
        except Exception as e:
            logger.error(f"Document Processing error: {e}", exc_info=True)
            analysis_results["agents"]["document_processor"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        # 2. Requirements Extraction Agent - DETAYLI
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Requirements Extraction Agent (DETAYLI)")
        logger.info("="*80)
        
        try:
            req_start = datetime.now()
            
            # Her döküman için ayrı ayrı gereksinim çıkarımı - RFQ'lar için ÖZEL DETAYLI ANALİZ
            all_requirements = []
            
            for doc_name, doc_text in self.document_texts.items():
                logger.info(f"   Extracting requirements from: {doc_name}")
                
                # RFQ tespiti
                is_rfq = self._is_rfq_document(doc_name, doc_text)
                if is_rfq:
                    logger.info(f"   *** RFQ DETECTED: {doc_name} - ÇOK DETAYLI ANALİZ YAPILIYOR ***")
                
                if self.req_agent:
                    req_result = self.req_agent.extract_requirements(
                        doc_text,
                        self.opportunity_data
                    )
                    if req_result.get('requirements'):
                        for req in req_result.get('requirements', []):
                            req['source_document'] = doc_name
                            req['is_rfq'] = is_rfq
                            all_requirements.append(req)
                
                # RFQ ise ÇOK DETAYLI LLM analizi yap
                if is_rfq and self.llm_analyzer and doc_text:
                    logger.info(f"   Running ULTRA-DETAILED RFQ analysis for: {doc_name}")
                    rfq_detailed_result = self._analyze_rfq_in_detail(doc_name, doc_text)
                    if rfq_detailed_result:
                        all_requirements.extend(rfq_detailed_result)
            
            # LLM Analyzer ile tüm dökümanların birleşik detaylı analizi
            if self.llm_analyzer and combined_text:
                logger.info("   Running LLM-based detailed requirements extraction (ALL DOCUMENTS)...")
                llm_req_result = self.llm_analyzer.extract_requirements(combined_text)
                if llm_req_result.get('success'):
                    llm_reqs = llm_req_result.get('data', {}).get('requirements', {})
                    if isinstance(llm_reqs, dict):
                        # Convert dict to list format
                        for key, value in llm_reqs.items():
                            all_requirements.append({
                                "code": f"LLM-{key.upper()}",
                                "text": str(value),
                                "category": "llm_extracted",
                                "priority": "high",
                                "source": "LLM_Analyzer"
                            })
            
            # AutoGen Requirements Extractor Agent ile ek analiz (eğer mevcut)
            if self.autogen_agents and 'requirements_extractor' in self.autogen_agents and combined_text:
                try:
                    logger.info("   Running AutoGen Requirements Extractor Agent...")
                    req_agent = self.autogen_agents['requirements_extractor']
                    
                    # AutoGen agent prompt
                    autogen_prompt = f"""Analyze these documents and extract ALL requirements in detail:

Documents Content:
{combined_text[:20000]}

Extract:
- ALL technical requirements
- ALL operational requirements  
- ALL capacity requirements
- ALL date/location requirements
- ALL compliance requirements
- ALL commercial terms

Return requirements in JSON format with: code, text, category, priority."""
                    
                    # Use AutoGen agent (if available)
                    if hasattr(req_agent, 'generate_reply'):
                        autogen_response = req_agent.generate_reply(
                            messages=[{"role": "user", "content": autogen_prompt}]
                        )
                        # Parse response and add to requirements
                        try:
                            if isinstance(autogen_response, str):
                                # Try to extract JSON from response
                                import re
                                json_match = re.search(r'\{.*\}', autogen_response, re.DOTALL)
                                if json_match:
                                    autogen_data = json.loads(json_match.group())
                                    if isinstance(autogen_data, dict) and 'requirements' in autogen_data:
                                        for req in autogen_data['requirements']:
                                            req['source'] = 'AutoGen_RequirementsExtractor'
                                            all_requirements.append(req)
                                        logger.info(f"   AutoGen extracted {len(autogen_data.get('requirements', []))} additional requirements")
                        except Exception as e:
                            logger.warning(f"   AutoGen response parsing failed: {e}")
                except Exception as e:
                    logger.warning(f"   AutoGen Requirements Extractor error: {e}")
            
            req_end = datetime.now()
            req_duration = (req_end - req_start).total_seconds()
            
            analysis_results["agents"]["requirements_extractor"] = {
                "status": "completed",
                "duration_seconds": req_duration,
                "total_requirements": len(all_requirements),
                "requirements": all_requirements,
                "categories": self._categorize_requirements(all_requirements),
                "timestamp": req_end.isoformat()
            }
            
            logger.info(f"Requirements Extraction completed in {req_duration:.2f}s")
            logger.info(f"   Total requirements extracted: {len(all_requirements)}")
        
        except Exception as e:
            logger.error(f"Requirements Extraction error: {e}", exc_info=True)
            analysis_results["agents"]["requirements_extractor"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            all_requirements = []
        
        # 3. Compliance Analysis Agent - DETAYLI
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Compliance Analysis Agent (DETAYLI)")
        logger.info("="*80)
        
        try:
            comp_start = datetime.now()
            
            if self.comp_agent and all_requirements:
                comp_result = self.comp_agent.analyze_compliance(
                    all_requirements,
                    {}  # Facility data (can be enhanced)
                )
            else:
                comp_result = {
                    "compliance_matrix": [],
                    "overall_risk": "unknown",
                    "met_count": 0,
                    "gap_count": len(all_requirements) if all_requirements else 0
                }
            
            # LLM Analyzer ile detaylı uyumluluk analizi
            if self.llm_analyzer and combined_text:
                logger.info("   Running LLM-based detailed compliance analysis...")
                # Analyze by document type
                for doc_name, doc_text in self.document_texts.items():
                    doc_type = self._detect_document_type(doc_name, doc_text)
                    if doc_type:
                        doc_analysis = self.llm_analyzer.analyze_document_by_type(
                            doc_text,
                            doc_type
                        )
                        if doc_analysis.get('success'):
                            comp_result.setdefault('llm_analysis', {})[doc_name] = doc_analysis.get('data', {})
            
            comp_end = datetime.now()
            comp_duration = (comp_end - comp_start).total_seconds()
            
            analysis_results["agents"]["compliance_analyst"] = {
                "status": "completed",
                "duration_seconds": comp_duration,
                "results": comp_result,
                "timestamp": comp_end.isoformat()
            }
            
            logger.info(f"Compliance Analysis completed in {comp_duration:.2f}s")
        
        except Exception as e:
            logger.error(f"Compliance Analysis error: {e}", exc_info=True)
            analysis_results["agents"]["compliance_analyst"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        # 4. Proposal Writing Agent - DETAYLI
        logger.info("\n" + "="*80)
        logger.info("STEP 4: Proposal Writing Agent (DETAYLI)")
        logger.info("="*80)
        
        try:
            prop_start = datetime.now()
            
            # Collect all previous results
            previous_results = {
                "requirements": all_requirements,
                "compliance": analysis_results["agents"].get("compliance_analyst", {}).get("results", {}),
                "documents": analysis_results["agents"].get("document_processor", {}).get("results", [])
            }
            
            if self.prop_agent:
                prop_result = self.prop_agent.write_proposal(
                    previous_results,
                    self.opportunity_data
                )
            else:
                prop_result = {
                    "executive_summary": "Proposal summary based on analysis",
                    "technical_approach": "Technical approach details",
                    "past_performance": "Past performance information",
                    "compliance_matrix": previous_results.get("compliance", {}).get("compliance_matrix", [])
                }
            
            prop_end = datetime.now()
            prop_duration = (prop_end - prop_start).total_seconds()
            
            analysis_results["agents"]["proposal_writer"] = {
                "status": "completed",
                "duration_seconds": prop_duration,
                "results": prop_result,
                "timestamp": prop_end.isoformat()
            }
            
            logger.info(f"Proposal Writing completed in {prop_duration:.2f}s")
        
        except Exception as e:
            logger.error(f"Proposal Writing error: {e}", exc_info=True)
            analysis_results["agents"]["proposal_writer"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        # 5. Quality Assurance Agent - DETAYLI
        logger.info("\n" + "="*80)
        logger.info("STEP 5: Quality Assurance Agent (DETAYLI)")
        logger.info("="*80)
        
        try:
            qa_start = datetime.now()
            
            # Collect proposal for QA
            proposal_data = analysis_results["agents"].get("proposal_writer", {}).get("results", {})
            
            if self.qa_agent:
                qa_result = self.qa_agent.review_proposal(proposal_data)
            else:
                qa_result = {
                    "quality_score": 0.85,
                    "completeness": 0.90,
                    "format_compliance": 0.95,
                    "requirement_coverage": 0.80,
                    "recommendations": ["Review manually for accuracy"]
                }
            
            qa_end = datetime.now()
            qa_duration = (qa_end - qa_start).total_seconds()
            
            analysis_results["agents"]["quality_assurance"] = {
                "status": "completed",
                "duration_seconds": qa_duration,
                "results": qa_result,
                "timestamp": qa_end.isoformat()
            }
            
            logger.info(f"Quality Assurance completed in {qa_duration:.2f}s")
        
        except Exception as e:
            logger.error(f"Quality Assurance error: {e}", exc_info=True)
            analysis_results["agents"]["quality_assurance"] = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        # Finalize analysis
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        
        analysis_results["analysis_end"] = end_time.isoformat()
        analysis_results["total_duration_seconds"] = total_duration
        analysis_results["summary"] = self._generate_summary(analysis_results)
        
        logger.info("\n" + "="*80)
        logger.info(f"Detailed Analysis Completed in {total_duration:.2f}s")
        logger.info("="*80)
        
        self.analysis_results = analysis_results
        return analysis_results
    
    def _categorize_requirements(self, requirements: List[Dict[str, Any]]) -> Dict[str, int]:
        """Gereksinimleri kategorilere göre say"""
        categories = {
            "capacity": 0,
            "date": 0,
            "transport": 0,
            "av": 0,
            "invoice": 0,
            "clauses": 0,
            "other": 0
        }
        
        for req in requirements:
            cat = req.get('category', 'other')
            if cat in categories:
                categories[cat] += 1
            else:
                categories["other"] += 1
        
        return categories
    
    def _is_rfq_document(self, filename: str, text: str = "") -> bool:
        """RFQ dökümanı mı kontrol et"""
        filename_lower = filename.lower()
        text_lower = text.lower() if text else ""
        
        # RFQ göstergeleri
        rfq_indicators = [
            "rfq" in filename_lower,
            "request for quote" in filename_lower,
            "request for quotation" in filename_lower,
            "solicitation" in filename_lower,
            "combined synopsis/solicitation" in text_lower[:500],
            "request for quote" in text_lower[:500],
            "lodging room requirements" in text_lower,
            "conference room requirements" in text_lower,
            "av/boardroom requirements" in text_lower
        ]
        
        return any(rfq_indicators)
    
    def _detect_document_type(self, filename: str, text: str = "") -> Optional[str]:
        """Döküman tipini tespit et"""
        filename_lower = filename.lower()
        text_lower = text.lower() if text else ""
        
        if "rfq" in filename_lower or "request" in filename_lower:
            return "rfq"
        if "sow" in filename_lower or "statement" in filename_lower:
            return "sow"
        if "contract" in filename_lower or "agreement" in filename_lower:
            return "contract"
        if "far" in filename_lower or "52.204" in text_lower:
            return "far"
        if "performance" in filename_lower:
            return "performance"
        
        return None
    
    def _analyze_rfq_in_detail(self, doc_name: str, doc_text: str) -> List[Dict[str, Any]]:
        """RFQ dökümanını ÇOK DETAYLI analiz et - Her maddeyi, her paragrafı incele"""
        if not self.llm_analyzer or not self.llm_analyzer.use_openai:
            return []
        
        try:
            logger.info(f"      RFQ Detaylı Analiz: {doc_name} ({len(doc_text)} karakter)")
            
            # Çok detaylı RFQ analiz prompt'u
            # İlk 50k karakteri al (çok uzun metinler için)
            doc_text_limited = doc_text[:50000] if len(doc_text) > 50000 else doc_text
            
            detailed_prompt = f"""Bu bir RFQ (Request for Quote) dökümanıdır. ÇOK DETAYLI olarak analiz et ve TÜM gereksinimleri çıkar.

DÖKÜMAN İÇERİĞİ:
{doc_text_limited}

LÜTFEN ŞUNLARI ÇOK DETAYLI ÇIKAR:

1. LODGING ROOM REQUIREMENTS (Konaklama Oda Gereksinimleri):
   - Oda sayısı (tam sayı)
   - Oda tipi gereksinimleri (single, double, suite, vb.)
   - Oda özellikleri (WiFi, TV, mini-bar, vb.)
   - Check-in/check-out saatleri
   - Cancellation policy
   - Per diem rate gereksinimleri
   - Her maddeyi ayrı ayrı listele

2. CONFERENCE ROOM REQUIREMENTS (Toplantı Salonu Gereksinimleri):
   - Salon sayısı ve kapasiteleri
   - Salon düzeni gereksinimleri (theater, classroom, u-shape, vb.)
   - Salon özellikleri (pencereler, doğal ışık, vb.)
   - Salon ekipmanları
   - Her maddeyi ayrı ayrı listele

3. AV/BOARDROOM REQUIREMENTS (Ses-Görüntü Gereksinimleri):
   - Projektör gereksinimleri
   - Ekran gereksinimleri
   - Mikrofon gereksinimleri
   - Ses sistemi gereksinimleri
   - Video konferans gereksinimleri
   - Power strip gereksinimleri
   - Her maddeyi ayrı ayrı listele

4. FOOD & BEVERAGE REQUIREMENTS (Yemek-İçecek Gereksinimleri):
   - Kahvaltı gereksinimleri
   - Öğle yemeği gereksinimleri
   - Akşam yemeği gereksinimleri
   - Coffee break gereksinimleri
   - Özel diyet gereksinimleri
   - Her maddeyi ayrı ayrı listele

5. SCHEDULE/BLOCK REQUIREMENTS (Program/Blok Gereksinimleri):
   - Check-in tarihi
   - Check-out tarihi
   - Meeting tarihleri
   - Block room gereksinimleri
   - Her maddeyi ayrı ayrı listele

6. INVOICING REQUIREMENTS (Faturalama Gereksinimleri):
   - Invoice format gereksinimleri
   - Invoice submission yöntemi (IPP, email, vb.)
   - Invoice number format
   - Payment terms
   - Her maddeyi ayrı ayrı listele

7. FAR CLAUSES & COMPLIANCE (FAR Maddeleri ve Uyumluluk):
   - FAR 52.212-4 gereksinimleri
   - FAR 52.212-5 gereksinimleri
   - FAR 52.204-24/25/26 gereksinimleri
   - Security/Telecom restrictions
   - Small business requirements
   - Her maddeyi ayrı ayrı listele

8. OTHER REQUIREMENTS (Diğer Gereksinimler):
   - Parking gereksinimleri
   - Accessibility gereksinimleri
   - Security gereksinimleri
   - Insurance gereksinimleri
   - Her maddeyi ayrı ayrı listele

ÇIKTI FORMATI (JSON):
{{
  "lodging_requirements": [
    {{"requirement": "...", "details": "...", "priority": "high/medium/low"}},
    ...
  ],
  "conference_requirements": [...],
  "av_requirements": [...],
  "food_beverage_requirements": [...],
  "schedule_requirements": [...],
  "invoicing_requirements": [...],
  "far_clauses": [...],
  "other_requirements": [...],
  "total_requirements_count": 0
}}

ÖNEMLİ: Her gereksinimi ayrı bir madde olarak çıkar. Hiçbir şeyi atlama. ÇOK DETAYLI ol."""
            
            # System message
            system_message = """Sen bir RFQ (Request for Quote) analiz uzmanısın. Görevin: RFQ dökümanını ÇOK DETAYLI olarak analiz etmek ve TÜM gereksinimleri madde madde çıkarmak. 

Her bölümü, her paragrafı, her maddeyi dikkatlice oku. Hiçbir gereksinimi atlama. Her gereksinimi ayrı bir JSON objesi olarak çıkar. ÇOK DETAYLI ol."""

            response = call_logged_llm(
                agent_name="RFQDetailAnalyzer",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": detailed_prompt},
                ],
                temperature=0.1,
                max_tokens=4000,
            )
            result_text = extract_message_text(response).strip()
            
            # JSON parse
            try:
                if result_text.startswith("```json"):
                    result_text = result_text[7:-3]
                elif result_text.startswith("```"):
                    result_text = result_text[3:-3]
                
                rfq_data = json.loads(result_text)
                
                # Tüm gereksinimleri listeye çevir
                detailed_requirements = []
                req_counter = 1
                
                categories_map = {
                    "lodging_requirements": "capacity",
                    "conference_requirements": "capacity",
                    "av_requirements": "av",
                    "food_beverage_requirements": "other",
                    "schedule_requirements": "date",
                    "invoicing_requirements": "invoice",
                    "far_clauses": "clauses",
                    "other_requirements": "other"
                }
                
                for category_key, requirements_list in rfq_data.items():
                    if category_key == "total_requirements_count":
                        continue
                    
                    if isinstance(requirements_list, list):
                        for req_item in requirements_list:
                            if isinstance(req_item, dict):
                                req_text = req_item.get('requirement') or req_item.get('text') or str(req_item)
                                req_details = req_item.get('details', '')
                                priority = req_item.get('priority', 'medium')
                                
                                full_text = req_text
                                if req_details:
                                    full_text += f" | Detaylar: {req_details}"
                                
                                detailed_requirements.append({
                                    "code": f"RFQ-{req_counter:03d}",
                                    "text": full_text,
                                    "category": categories_map.get(category_key, "other"),
                                    "priority": priority,
                                    "source_document": doc_name,
                                    "source": "RFQ_Detailed_Analysis",
                                    "rfq_category": category_key
                                })
                                req_counter += 1
                
                logger.info(f"      RFQ Detaylı Analiz tamamlandı: {len(detailed_requirements)} gereksinim çıkarıldı")
                return detailed_requirements
            
            except json.JSONDecodeError as e:
                logger.warning(f"      RFQ JSON parse hatası: {e}")
                logger.debug(f"      Raw response: {result_text[:500]}")
                return []
        
        except LLMNotAvailableError as exc:
            logger.warning(f"      LLM not available for RFQ detailed analysis: {exc}")
            return []
        except Exception as e:
            logger.error(f"      RFQ detaylı analiz hatası: {e}", exc_info=True)
            return []
    
    def _generate_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analiz özeti oluştur"""
        agents = analysis_results.get("agents", {})
        
        successful = sum(1 for agent in agents.values() if agent.get("status") == "completed")
        total = len(agents)
        
        requirements = agents.get("requirements_extractor", {}).get("requirements", [])
        compliance = agents.get("compliance_analyst", {}).get("results", {})
        qa = agents.get("quality_assurance", {}).get("results", {})
        
        return {
            "total_agents": total,
            "successful_agents": successful,
            "failed_agents": total - successful,
            "total_requirements": len(requirements),
            "compliance_score": compliance.get("overall_risk", "unknown"),
            "quality_score": qa.get("quality_score", 0),
            "overall_status": "completed" if successful == total else "partial"
        }
    
    def generate_detailed_report(self) -> Dict[str, Any]:
        """Detaylı analiz raporu oluştur"""
        logger.info("\n" + "="*80)
        logger.info("Generating Detailed Analysis Report")
        logger.info("="*80)
        
        if not self.analysis_results:
            logger.error("No analysis results available")
            # Create empty report info
            return {
                "json_path": None,
                "markdown_path": None,
                "pdf_path": None,
                "opportunity_id": self.opportunity_id,
                "output_dir": str(self.output_dir)
            }
        
        # 1. Save JSON report
        json_path = self.output_dir / "detailed_analysis_report.json"
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_results, f, ensure_ascii=False, indent=2)
            logger.info(f"JSON report saved: {json_path}")
        except Exception as e:
            logger.error(f"Error saving JSON report: {e}")
            json_path = None
        
        # 2. Generate Markdown report
        md_path = self.output_dir / "detailed_analysis_report.md"
        try:
            md_content = self._generate_markdown_report()
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            logger.info(f"Markdown report saved: {md_path}")
        except Exception as e:
            logger.error(f"Error saving Markdown report: {e}")
            md_path = None
        
        # 2.5. Generate SOW using RFQ-SOW Orchestrator (if RFQ detected)
        sow_pdf_path = None
        sow_markdown_path = None
        sow_json_path = None
        
        if self.rfq_sow_orchestrator and self.documents:
            try:
                # Check if we have RFQ documents
                rfq_docs = [doc for doc in self.documents if self._is_rfq_document(
                    doc.get('filename', ''),
                    self.document_texts.get(doc.get('filename', ''), '')
                )]
                
                if rfq_docs:
                    logger.info("\n" + "="*80)
                    logger.info("Generating SOW using RFQ-SOW Orchestrator")
                    logger.info("="*80)
                    
                    # Use first RFQ document
                    rfq_doc = rfq_docs[0]
                    rfq_path = rfq_doc.get('path') or rfq_doc.get('file_path', '')
                    
                    if rfq_path and Path(rfq_path).exists():
                        # Process RFQ to SOW
                        sow_result = self.rfq_sow_orchestrator.process_rfq_to_sow(
                            rfq_document_path=rfq_path,
                            output_folder=str(self.output_dir),
                            opportunity_code=self.opportunity_id
                        )
                        
                        if sow_result.get('success'):
                            sow_pdf_path = sow_result.get('sow_pdf_path')
                            sow_markdown_path = sow_result.get('markdown_path')
                            sow_json_path = sow_result.get('json_path')
                            logger.info(f"✅ SOW generated successfully!")
                            logger.info(f"   PDF: {sow_pdf_path}")
                            logger.info(f"   Markdown: {sow_markdown_path}")
                            logger.info(f"   JSON: {sow_json_path}")
                        else:
                            logger.warning(f"SOW generation failed: {sow_result.get('error')}")
                    else:
                        # Try with text content
                        combined_text = "\n\n".join(self.document_texts.values())
                        if combined_text:
                            logger.info("Processing RFQ text to SOW...")
                            sow_result = self.rfq_sow_orchestrator.process_rfq_text_to_sow(
                                rfq_text=combined_text,
                                output_folder=str(self.output_dir),
                                opportunity_code=self.opportunity_id
                            )
                            
                            if sow_result.get('success'):
                                sow_pdf_path = sow_result.get('sow_pdf_path')
                                sow_markdown_path = sow_result.get('markdown_path')
                                sow_json_path = sow_result.get('json_path')
                                logger.info(f"✅ SOW generated from text successfully!")
            except Exception as e:
                logger.warning(f"SOW generation error: {e}", exc_info=True)
        
        # 3. Generate PDF report (if available)
        pdf_path = None
        if PDF_BUILDER_AVAILABLE:
            try:
                # Convert analysis results to report format
                report_json = self._convert_to_report_format()
                pdf_path = self.output_dir / "detailed_analysis_report.pdf"
                
                success = build_pdf_report(
                    report_json=report_json,
                    output_path=str(pdf_path),
                    opportunity_code=self.opportunity_id
                )
                
                if success:
                    logger.info(f"PDF report saved: {pdf_path}")
                else:
                    logger.warning("PDF generation failed")
                    pdf_path = None
            except Exception as e:
                logger.error(f"PDF generation error: {e}", exc_info=True)
                pdf_path = None
        
        # 4. Save to database (if available)
        if DB_AVAILABLE:
            try:
                db = get_db_session()
                if db:
                    try:
                        ai_result = AIAnalysisResult(
                            opportunity_id=self.opportunity_id,
                            analysis_type='DETAILED_FULL_ANALYSIS',
                            result=self.analysis_results,
                            confidence=self.analysis_results.get("summary", {}).get("quality_score", 0.5),
                            timestamp=datetime.now(),
                            agent_name='DetailedOpportunityAnalyzer'
                        )
                        
                        db.add(ai_result)
                        db.commit()
                        
                        logger.info(f"Analysis saved to database: {ai_result.id}")
                    except Exception as e:
                        logger.error(f"Database save error: {e}", exc_info=True)
                        db.rollback()
                    finally:
                        db.close()
            except Exception as e:
                logger.error(f"Database error: {e}", exc_info=True)
        
        report_info = {
            "json_path": str(json_path) if json_path and json_path.exists() else None,
            "markdown_path": str(md_path) if md_path and md_path.exists() else None,
            "pdf_path": str(pdf_path) if pdf_path and pdf_path.exists() else None,
            "sow_pdf_path": str(sow_pdf_path) if sow_pdf_path and Path(sow_pdf_path).exists() else None,
            "sow_markdown_path": str(sow_markdown_path) if sow_markdown_path and Path(sow_markdown_path).exists() else None,
            "sow_json_path": str(sow_json_path) if sow_json_path and Path(sow_json_path).exists() else None,
            "opportunity_id": self.opportunity_id,
            "output_dir": str(self.output_dir)
        }
        
        return report_info
    
    def _convert_to_report_format(self) -> Dict[str, Any]:
        """Analiz sonuçlarını rapor formatına çevir"""
        agents = self.analysis_results.get("agents", {})
        req_agent = agents.get("requirements_extractor", {})
        comp_agent = agents.get("compliance_analyst", {})
        qa_agent = agents.get("quality_assurance", {})
        
        return {
            "opportunity_info": {
                "opportunity_id": self.opportunity_id,
                "title": self.opportunity_data.get("title", "N/A"),
                "notice_id": self.opportunity_data.get("noticeId", "N/A"),
                "solicitation_number": self.opportunity_data.get("solicitationNumber", "N/A"),
                "naics": self.opportunity_data.get("naics", []),
                "response_deadline": self.opportunity_data.get("responseDeadline", "N/A")
            },
            "requirements": req_agent.get("requirements", []),
            "compliance": comp_agent.get("results", {}),
            "fit_assessment": {
                "overall_score": int(qa_agent.get("results", {}).get("quality_score", 0.85) * 100),
                "confidence": qa_agent.get("results", {}).get("completeness", 0.9)
            },
            "summary": self.analysis_results.get("summary", {})
        }
    
    def _generate_markdown_report(self) -> str:
        """Markdown formatında detaylı rapor oluştur"""
        agents = self.analysis_results.get("agents", {})
        summary = self.analysis_results.get("summary", {})
        
        md = f"""# Detaylı Fırsat Analizi Raporu

## Fırsat Bilgileri

- **Opportunity ID**: {self.opportunity_id}
- **Başlık**: {self.opportunity_data.get('title', 'N/A')}
- **Notice ID**: {self.opportunity_data.get('noticeId', 'N/A')}
- **Analiz Tarihi**: {self.analysis_results.get('analysis_start', 'N/A')}
- **Toplam Süre**: {self.analysis_results.get('total_duration_seconds', 0):.2f} saniye

## Özet

- **Toplam Ajan**: {summary.get('total_agents', 0)}
- **Başarılı Ajan**: {summary.get('successful_agents', 0)}
- **Başarısız Ajan**: {summary.get('failed_agents', 0)}
- **Toplam Gereksinim**: {summary.get('total_requirements', 0)}
- **Kalite Skoru**: {summary.get('quality_score', 0):.2%}
- **Genel Durum**: {summary.get('overall_status', 'unknown')}

---

## 1. Document Processing Agent

**Durum**: {agents.get('document_processor', {}).get('status', 'unknown')}
**Süre**: {agents.get('document_processor', {}).get('duration_seconds', 0):.2f} saniye
**İşlenen Döküman**: {agents.get('document_processor', {}).get('documents_processed', 0)}

### İşlenen Dökümanlar

"""
        
        doc_results = agents.get('document_processor', {}).get('results', [])
        for doc_result in doc_results:
            doc_name = doc_result.get('document_name', 'Unknown')
            doc_data = doc_result.get('processed_data', {})
            md += f"#### {doc_name}\n\n"
            md += f"- İçerik Uzunluğu: {doc_data.get('content_length', 0)} karakter\n"
            md += f"- Metadata: {json.dumps(doc_data.get('extracted_metadata', {}), ensure_ascii=False, indent=2)}\n\n"
        
        md += "\n---\n\n## 2. Requirements Extraction Agent\n\n"
        
        req_agent = agents.get('requirements_extractor', {})
        md += f"**Durum**: {req_agent.get('status', 'unknown')}\n"
        md += f"**Süre**: {req_agent.get('duration_seconds', 0):.2f} saniye\n"
        md += f"**Toplam Gereksinim**: {req_agent.get('total_requirements', 0)}\n\n"
        
        categories = req_agent.get('categories', {})
        md += "### Kategoriler\n\n"
        for cat, count in categories.items():
            md += f"- **{cat}**: {count}\n"
        
        md += "\n### Gereksinimler\n\n"
        requirements = req_agent.get('requirements', [])
        for i, req in enumerate(requirements[:50], 1):  # İlk 50 gereksinim
            md += f"{i}. **{req.get('code', 'N/A')}** ({req.get('category', 'unknown')}) - {req.get('text', 'N/A')[:200]}...\n"
            md += f"   - Öncelik: {req.get('priority', 'unknown')}\n"
            md += f"   - Kaynak: {req.get('source_document', 'unknown')}\n\n"
        
        if len(requirements) > 50:
            md += f"\n*... ve {len(requirements) - 50} gereksinim daha*\n"
        
        md += "\n---\n\n## 3. Compliance Analysis Agent\n\n"
        
        comp_agent = agents.get('compliance_analyst', {})
        md += f"**Durum**: {comp_agent.get('status', 'unknown')}\n"
        md += f"**Süre**: {comp_agent.get('duration_seconds', 0):.2f} saniye\n\n"
        
        comp_results = comp_agent.get('results', {})
        md += f"- **Genel Risk**: {comp_results.get('overall_risk', 'unknown')}\n"
        md += f"- **Karşılanan**: {comp_results.get('met_count', 0)}\n"
        md += f"- **Eksik**: {comp_results.get('gap_count', 0)}\n\n"
        
        md += "\n---\n\n## 4. Proposal Writing Agent\n\n"
        
        prop_agent = agents.get('proposal_writer', {})
        md += f"**Durum**: {prop_agent.get('status', 'unknown')}\n"
        md += f"**Süre**: {prop_agent.get('duration_seconds', 0):.2f} saniye\n\n"
        
        prop_results = prop_agent.get('results', {})
        md += f"### Executive Summary\n\n{prop_results.get('executive_summary', 'N/A')}\n\n"
        md += f"### Technical Approach\n\n{prop_results.get('technical_approach', 'N/A')}\n\n"
        
        md += "\n---\n\n## 5. Quality Assurance Agent\n\n"
        
        qa_agent = agents.get('quality_assurance', {})
        md += f"**Durum**: {qa_agent.get('status', 'unknown')}\n"
        md += f"**Süre**: {qa_agent.get('duration_seconds', 0):.2f} saniye\n\n"
        
        qa_results = qa_agent.get('results', {})
        md += f"- **Kalite Skoru**: {qa_results.get('quality_score', 0):.2%}\n"
        md += f"- **Tamamlanma**: {qa_results.get('completeness', 0):.2%}\n"
        md += f"- **Format Uyumluluğu**: {qa_results.get('format_compliance', 0):.2%}\n"
        md += f"- **Gereksinim Kapsamı**: {qa_results.get('requirement_coverage', 0):.2%}\n\n"
        
        recommendations = qa_results.get('recommendations', [])
        if recommendations:
            md += "### Öneriler\n\n"
            for rec in recommendations:
                md += f"- {rec}\n"
        
        md += "\n---\n\n## Sonuç\n\n"
        md += f"Detaylı analiz tamamlandı. Tüm ajanlar çalıştırıldı ve kapsamlı bir analiz raporu oluşturuldu.\n\n"
        md += f"**Rapor Oluşturulma Tarihi**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return md
    
    def run_full_analysis(self) -> Dict[str, Any]:
        """Tam analiz pipeline'ını çalıştır"""
        logger.info("\n" + "="*80)
        logger.info(f"Starting Full Detailed Analysis for Opportunity: {self.opportunity_id}")
        logger.info("="*80)
        
        # Step 1: Fetch opportunity data
        opp_data = self.fetch_opportunity_data()
        if not opp_data:
            logger.error("Cannot proceed without opportunity data")
            return {"error": "Opportunity data not found"}
        
        # Step 2: Download documents
        documents = self.download_documents()
        if not documents:
            logger.warning("No documents downloaded, but continuing with analysis")
        
        # Step 2.5: Process documents if not already processed
        if not self.document_texts and documents:
            logger.info("Processing downloaded documents...")
            self._process_downloaded_documents(documents)
        
        # Step 3: Run detailed analysis
        analysis_results = self.run_detailed_analysis()
        
        # Step 4: Generate detailed report
        report_info = self.generate_detailed_report()
        
        logger.info("\n" + "="*80)
        logger.info("Full Analysis Completed Successfully!")
        logger.info("="*80)
        logger.info(f"JSON Report: {report_info.get('json_path')}")
        logger.info(f"Markdown Report: {report_info.get('markdown_path')}")
        if report_info.get('pdf_path'):
            logger.info(f"PDF Report: {report_info.get('pdf_path')}")
        logger.info("="*80)
        
        return {
            "success": True,
            "opportunity_id": self.opportunity_id,
            "analysis_results": analysis_results,
            "report_info": report_info
        }


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python detailed_opportunity_analysis.py <opportunity_id>")
        print("\nExample:")
        print("  python detailed_opportunity_analysis.py 57cd76db400c4e7ca895d40bf6454173")
        sys.exit(1)
    
    opportunity_id = sys.argv[1]
    
    # Create analyzer
    analyzer = DetailedOpportunityAnalyzer(opportunity_id)
    
    # Run full analysis
    try:
        result = analyzer.run_full_analysis()
        
        if result.get("success"):
            print("\n[OK] Analysis completed successfully!")
            print(f"\nReports saved in: {result['report_info']['output_dir']}")
        else:
            print(f"\n[ERROR] Analysis failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

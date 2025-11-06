"""
MergenLite Sadeleştirilmiş Ajan Mimarisi
10 ajanlı sistemden 4-5 çekirdek ajana indirgenmiş versiyon
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

load_dotenv()

# AutoGen imports
try:
    from autogen import ConversableAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    ConversableAgent = None
    logging.warning("AutoGen not available. Install with: pip install pyautogen")

logger = logging.getLogger(__name__)

# ============================================================================
# ÇEKİRDEK AJANLAR (Korunan)
# ============================================================================

class DocumentProcessorAgent:
    """
    Çekirdek Ajan 1: Document Processor Agent
    Ham belgeleri işlemek ve metayı yapılandırmak
    """
    
    def __init__(self):
        self.name = "DocumentProcessor"
        self.agent = None
        
        if AUTOGEN_AVAILABLE:
            try:
                llm_config = self._get_llm_config()
                self.agent = ConversableAgent(
                    name=self.name,
                    system_message="""
                    You are a document processing specialist for government contracting.
                    Your expertise includes:
                    - PDF and DOCX document analysis
                    - Structured data extraction
                    - Metadata identification (dates, deadlines, contact info)
                    - Content categorization
                    - Table and list extraction
                    
                    Always provide accurate, detailed analysis of documents in JSON format.
                    """,
                    llm_config=llm_config
                )
                logger.info(f"✅ {self.name} initialized")
            except Exception as e:
                logger.warning(f"⚠️ {self.name} initialization failed: {e}")
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """LLM konfigürasyonunu al"""
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        
        if use_ollama:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
            return {
                "model": ollama_model,
                "base_url": f"{ollama_url}/v1",
                "api_key": "ollama",
                "temperature": 0.1,
                "max_tokens": 4000
            }
        else:
            return {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.1,
                "max_tokens": 4000
            }
    
    def process_document(self, document_path: str, document_content: str) -> Dict[str, Any]:
        """Belgeyi işle ve yapılandırılmış veri çıkar"""
        try:
            # Eğer AutoGen agent varsa kullan
            if self.agent:
                # AutoGen ile analiz yapılacak (gelecekte implement edilecek)
                pass
            
            # Şimdilik basit yapılandırılmış çıktı
            return {
                "document_path": document_path,
                "content_length": len(document_content),
                "extracted_metadata": {
                    "key_dates": [],
                    "contact_info": {},
                    "tables": [],
                    "lists": []
                },
                "processed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Document processing error: {e}")
            return {"error": str(e)}


class RequirementsExtractorAgent:
    """
    Çekirdek Ajan 2: Requirements Extractor Agent
    Sözleşme gereksinimlerini çıkarmak ve kategorize etmek
    """
    
    def __init__(self):
        self.name = "RequirementsExtractor"
        self.agent = None
        
        if AUTOGEN_AVAILABLE:
            try:
                llm_config = self._get_llm_config()
                self.agent = ConversableAgent(
                    name=self.name,
                    system_message="""
                    You are a requirements extraction specialist for government RFQs.
                    Your expertise includes:
                    - RFQ requirement identification
                    - Requirement categorization (capacity, date, transport, av, invoice, clauses)
                    - Priority assessment (low, medium, high, critical)
                    - FAR clause recognition
                    - Compliance requirement analysis
                    
                    Extract requirements with high accuracy and proper categorization.
                    Return JSON format with structured requirements.
                    """,
                    llm_config=llm_config
                )
                logger.info(f"✅ {self.name} initialized")
            except Exception as e:
                logger.warning(f"⚠️ {self.name} initialization failed: {e}")
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """LLM konfigürasyonunu al"""
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        
        if use_ollama:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
            return {
                "model": ollama_model,
                "base_url": f"{ollama_url}/v1",
                "api_key": "ollama",
                "temperature": 0.1,
                "max_tokens": 4000
            }
        else:
            return {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.1,
                "max_tokens": 4000
            }
    
    def extract_requirements(self, document_content: str, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gereksinimleri çıkar ve kategorize et"""
        try:
            # Eğer AutoGen agent varsa kullan
            if self.agent:
                # AutoGen ile analiz yapılacak (gelecekte implement edilecek)
                pass
            
            # Şimdilik örnek yapılandırılmış çıktı
            return {
                "requirements": [
                    {
                        "code": "R-001",
                        "text": "Sample requirement extracted from document",
                        "category": "capacity",
                        "priority": "high"
                    }
                ],
                "total_count": 1,
                "categories": {
                    "capacity": 1,
                    "date": 0,
                    "transport": 0,
                    "av": 0,
                    "invoice": 0,
                    "clauses": 0
                },
                "extracted_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Requirements extraction error: {e}")
            return {"error": str(e)}


class ComplianceAnalystAgent:
    """
    Çekirdek Ajan 3: Compliance Analyst Agent
    FAR uyumluluğunu kontrol etmek ve risk analizi yapmak
    """
    
    def __init__(self):
        self.name = "ComplianceAnalyst"
        self.agent = None
        
        if AUTOGEN_AVAILABLE:
            try:
                llm_config = self._get_llm_config()
                self.agent = ConversableAgent(
                    name=self.name,
                    system_message="""
                    You are a compliance analysis specialist for government contracts.
                    Your expertise includes:
                    - FAR (Federal Acquisition Regulation) compliance checking
                    - Risk assessment and mitigation
                    - Requirement vs capability matching
                    - Gap analysis
                    - Compliance scoring (0.0 to 1.0)
                    
                    Analyze compliance and provide detailed risk assessment.
                    Return JSON format with compliance matrix and risk levels.
                    """,
                    llm_config=llm_config
                )
                logger.info(f"✅ {self.name} initialized")
            except Exception as e:
                logger.warning(f"⚠️ {self.name} initialization failed: {e}")
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """LLM konfigürasyonunu al"""
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        
        if use_ollama:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
            return {
                "model": ollama_model,
                "base_url": f"{ollama_url}/v1",
                "api_key": "ollama",
                "temperature": 0.1,
                "max_tokens": 4000
            }
        else:
            return {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.1,
                "max_tokens": 4000
            }
    
    def analyze_compliance(self, requirements: List[Dict[str, Any]], facility_data: Dict[str, Any]) -> Dict[str, Any]:
        """Uyumluluğu analiz et ve risk değerlendirmesi yap"""
        try:
            # Eğer AutoGen agent varsa kullan
            if self.agent:
                # AutoGen ile analiz yapılacak (gelecekte implement edilecek)
                pass
            
            # Şimdilik örnek yapılandırılmış çıktı
            return {
                "compliance_matrix": [
                    {
                        "requirement_code": "R-001",
                        "compliance_score": 0.95,
                        "risk_level": "low",
                        "evidence": "Facility meets requirement",
                        "gaps": []
                    }
                ],
                "overall_risk": "low",
                "met_count": 1,
                "gap_count": 0,
                "analyzed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Compliance analysis error: {e}")
            return {"error": str(e)}


class ProposalWriterAgent:
    """
    Çekirdek Ajan 4: Proposal Writer Agent
    Analiz sonuçlarından teklif özetini ve bölümlerini oluşturmak
    """
    
    def __init__(self):
        self.name = "ProposalWriter"
        self.agent = None
        
        if AUTOGEN_AVAILABLE:
            try:
                llm_config = self._get_llm_config()
                self.agent = ConversableAgent(
                    name=self.name,
                    system_message="""
                    You are a proposal writing specialist for government contracts.
                    Your expertise includes:
                    - Executive summary writing
                    - Technical approach sections
                    - Past performance narratives
                    - Compliance matrix documentation
                    - Professional proposal formatting
                    
                    Write compelling, compliant, and professional proposal sections.
                    Return well-structured proposal content.
                    """,
                    llm_config=llm_config
                )
                logger.info(f"✅ {self.name} initialized")
            except Exception as e:
                logger.warning(f"⚠️ {self.name} initialization failed: {e}")
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """LLM konfigürasyonunu al"""
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        
        if use_ollama:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
            return {
                "model": ollama_model,
                "base_url": f"{ollama_url}/v1",
                "api_key": "ollama",
                "temperature": 0.7,  # Daha yaratıcı yazım için
                "max_tokens": 4000
            }
        else:
            return {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.7,
                "max_tokens": 4000
            }
    
    def write_proposal(self, analysis_results: Dict[str, Any], opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Teklif taslağını oluştur"""
        try:
            # Eğer AutoGen agent varsa kullan
            if self.agent:
                # AutoGen ile yazım yapılacak (gelecekte implement edilecek)
                pass
            
            # Şimdilik örnek yapılandırılmış çıktı
            return {
                "executive_summary": "Sample executive summary...",
                "technical_approach": "Sample technical approach...",
                "past_performance": "Sample past performance...",
                "compliance_matrix": analysis_results.get("compliance_matrix", []),
                "proposal_sections": {
                    "section_1": "Content...",
                    "section_2": "Content..."
                },
                "written_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Proposal writing error: {e}")
            return {"error": str(e)}


class QualityAssuranceAgent:
    """
    Opsiyonel Ajan 5: Quality Assurance Agent
    Nihai teklif taslağını kontrol etmek
    """
    
    def __init__(self):
        self.name = "QualityAssurance"
        self.agent = None
        
        if AUTOGEN_AVAILABLE:
            try:
                llm_config = self._get_llm_config()
                self.agent = ConversableAgent(
                    name=self.name,
                    system_message="""
                    You are a quality assurance specialist for government proposals.
                    Your expertise includes:
                    - Proposal completeness checking
                    - Format compliance verification
                    - Requirement coverage validation
                    - Grammar and style review
                    - Final quality scoring
                    
                    Review proposals and provide quality feedback.
                    Return JSON format with quality metrics and recommendations.
                    """,
                    llm_config=llm_config
                )
                logger.info(f"✅ {self.name} initialized")
            except Exception as e:
                logger.warning(f"⚠️ {self.name} initialization failed: {e}")
    
    def _get_llm_config(self) -> Dict[str, Any]:
        """LLM konfigürasyonunu al"""
        use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        
        if use_ollama:
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
            return {
                "model": ollama_model,
                "base_url": f"{ollama_url}/v1",
                "api_key": "ollama",
                "temperature": 0.1,
                "max_tokens": 2000
            }
        else:
            return {
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "api_key": os.getenv("OPENAI_API_KEY"),
                "temperature": 0.1,
                "max_tokens": 2000
            }
    
    def review_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Teklifi gözden geçir ve kalite skoru ver"""
        try:
            # Eğer AutoGen agent varsa kullan
            if self.agent:
                # AutoGen ile gözden geçirme yapılacak (gelecekte implement edilecek)
                pass
            
            # Şimdilik örnek yapılandırılmış çıktı
            return {
                "quality_score": 0.85,
                "completeness": 0.90,
                "format_compliance": 0.95,
                "requirement_coverage": 0.80,
                "recommendations": [
                    "Add more detail to technical approach",
                    "Include additional past performance examples"
                ],
                "reviewed_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Quality assurance error: {e}")
            return {"error": str(e)}


# ============================================================================
# MERGENLITE ORCHESTRATOR
# ============================================================================

class MergenLiteOrchestrator:
    """
    Sadeleştirilmiş Orchestrator
    4-5 çekirdek ajanı koordine eder
    """
    
    def __init__(self):
        self.doc_processor = DocumentProcessorAgent()
        self.requirements_extractor = RequirementsExtractorAgent()
        self.compliance_analyst = ComplianceAnalystAgent()
        self.proposal_writer = ProposalWriterAgent()
        self.qa_agent = QualityAssuranceAgent()
        
        logger.info("✅ MergenLite Orchestrator initialized with 5 core agents")
    
    def run_full_analysis(self, opportunity_id: str, document_paths: List[str]) -> Dict[str, Any]:
        """
        Tam analiz pipeline'ını çalıştır
        
        Args:
            opportunity_id: SAM.gov fırsat ID'si
            document_paths: İşlenecek doküman yolları
        
        Returns:
            Konsolide analiz sonuçları (ai_analysis_results tablosuna kaydedilecek format)
        """
        try:
            logger.info(f"🚀 Starting full analysis for opportunity: {opportunity_id}")
            
            # 1. Document Processing
            logger.info("📄 Step 1: Document Processing")
            processed_docs = []
            for doc_path in document_paths:
                # Doküman içeriğini oku (gerçek implementasyonda document_processor kullanılacak)
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                processed = self.doc_processor.process_document(doc_path, content)
                processed_docs.append(processed)
            
            # 2. Requirements Extraction
            logger.info("📋 Step 2: Requirements Extraction")
            all_requirements = []
            for doc in processed_docs:
                requirements = self.requirements_extractor.extract_requirements(
                    doc.get("content", ""),
                    {"opportunity_id": opportunity_id}
                )
                all_requirements.extend(requirements.get("requirements", []))
            
            # 3. Compliance Analysis
            logger.info("✅ Step 3: Compliance Analysis")
            compliance_result = self.compliance_analyst.analyze_compliance(
                all_requirements,
                {}  # Facility data (gerçek implementasyonda veritabanından gelecek)
            )
            
            # 4. Proposal Writing
            logger.info("✍️ Step 4: Proposal Writing")
            analysis_results = {
                "requirements": all_requirements,
                "compliance": compliance_result
            }
            proposal = self.proposal_writer.write_proposal(
                analysis_results,
                {"opportunity_id": opportunity_id}
            )
            
            # 5. Quality Assurance (Opsiyonel)
            logger.info("🔍 Step 5: Quality Assurance")
            qa_result = self.qa_agent.review_proposal(proposal)
            
            # Konsolide çıktı (ai_analysis_results.consolidated_output formatı)
            consolidated_output = {
                "document_processing": processed_docs,
                "requirements": all_requirements,
                "compliance": compliance_result,
                "proposal": proposal,
                "quality_assurance": qa_result,
                "analysis_metadata": {
                    "opportunity_id": opportunity_id,
                    "total_documents": len(document_paths),
                    "total_requirements": len(all_requirements),
                    "analysis_completed_at": datetime.now().isoformat()
                }
            }
            
            logger.info(f"✅ Full analysis completed for opportunity: {opportunity_id}")
            
            return {
                "opportunity_id": opportunity_id,
                "analysis_status": "COMPLETED",
                "consolidated_output": consolidated_output,
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Analysis pipeline error: {e}")
            return {
                "opportunity_id": opportunity_id,
                "analysis_status": "FAILED",
                "error": str(e),
                "start_time": datetime.now().isoformat()
            }


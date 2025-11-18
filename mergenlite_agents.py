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

# MergenLite imports
try:
    from document_processor import process_documents_for_opportunity
except ImportError:
    process_documents_for_opportunity = None

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
        """Gereksinimleri çıkar ve kategorize et - GERÇEK ANALİZ"""
        try:
            # LLM Analyzer kullanarak gerçek analiz yap
            try:
                from llm_analyzer import LLMAnalyzer
                llm_analyzer = LLMAnalyzer()
                if llm_analyzer.use_openai and document_content:
                    # Gerçek LLM analizi
                    result = llm_analyzer.extract_requirements(document_content)
                    if result.get('success'):
                        reqs_data = result.get('data', {}).get('requirements', {})
                        if isinstance(reqs_data, dict):
                            # Dict formatını list formatına çevir
                            requirements = []
                            req_counter = 1
                            
                            # Oda sayısı
                            if reqs_data.get('room_count') and reqs_data.get('room_count') != 'belirtilmemiş':
                                requirements.append({
                                    "code": f"R-{req_counter:03d}",
                                    "text": f"Oda sayısı gereksinimi: {reqs_data.get('room_count')}",
                                    "category": "capacity",
                                    "priority": "high"
                                })
                                req_counter += 1
                            
                            # AV gereksinimi
                            if reqs_data.get('av_required'):
                                requirements.append({
                                    "code": f"R-{req_counter:03d}",
                                    "text": "Audio-Visual (AV) ekipman gereksinimi",
                                    "category": "av",
                                    "priority": "high"
                                })
                                req_counter += 1
                            
                            # Tarih aralığı
                            if reqs_data.get('date_range') and reqs_data.get('date_range') != 'belirtilmemiş':
                                requirements.append({
                                    "code": f"R-{req_counter:03d}",
                                    "text": f"Tarih aralığı: {reqs_data.get('date_range')}",
                                    "category": "date",
                                    "priority": "high"
                                })
                                req_counter += 1
                            
                            # Konum
                            if reqs_data.get('location') and reqs_data.get('location') != 'belirtilmemiş':
                                requirements.append({
                                    "code": f"R-{req_counter:03d}",
                                    "text": f"Konum gereksinimi: {reqs_data.get('location')}",
                                    "category": "transport",
                                    "priority": "high"
                                })
                                req_counter += 1
                            
                            # Kısıtlar
                            if reqs_data.get('constraints'):
                                for constraint in reqs_data.get('constraints', []):
                                    requirements.append({
                                        "code": f"R-{req_counter:03d}",
                                        "text": f"Kısıt: {constraint}",
                                        "category": "clauses",
                                        "priority": "medium"
                                    })
                                    req_counter += 1
                            
                            # Diğer gereksinimler
                            if reqs_data.get('other_requirements'):
                                for other_req in reqs_data.get('other_requirements', []):
                                    requirements.append({
                                        "code": f"R-{req_counter:03d}",
                                        "text": str(other_req),
                                        "category": "other",
                                        "priority": "medium"
                                    })
                                    req_counter += 1
                            
                            # Kategorilere göre say
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
                            
                            return {
                                "requirements": requirements,
                                "total_count": len(requirements),
                                "categories": categories,
                                "extracted_at": datetime.now().isoformat()
                            }
            except Exception as llm_error:
                logger.warning(f"LLM analyzer error, using pattern matching: {llm_error}")
            
            # Fallback: Pattern matching ile basit analiz
            requirements = []
            req_counter = 1
            text_lower = document_content.lower()
            
            # Oda sayısı
            import re
            room_match = re.search(r'(\d+)\s*(?:room|oda|bedroom)', text_lower)
            if room_match:
                requirements.append({
                    "code": f"R-{req_counter:03d}",
                    "text": f"Oda sayısı gereksinimi: {room_match.group(1)}",
                    "category": "capacity",
                    "priority": "high"
                })
                req_counter += 1
            
            # AV gereksinimi
            if any(keyword in text_lower for keyword in ['av', 'audio', 'visual', 'projector', 'screen', 'microphone']):
                requirements.append({
                    "code": f"R-{req_counter:03d}",
                    "text": "Audio-Visual (AV) ekipman gereksinimi",
                    "category": "av",
                    "priority": "high"
                })
                req_counter += 1
            
            # Tarih
            date_patterns = re.findall(r'\d{4}-\d{2}-\d{2}', document_content)
            if len(date_patterns) >= 2:
                requirements.append({
                    "code": f"R-{req_counter:03d}",
                    "text": f"Tarih aralığı: {date_patterns[0]} to {date_patterns[1]}",
                    "category": "date",
                    "priority": "high"
                })
                req_counter += 1
            
            # Kategorilere göre say
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
            
            return {
                "requirements": requirements if requirements else [{
                    "code": "R-001",
                    "text": "Dökümandan gereksinim çıkarılamadı (detaylı analiz gerekli)",
                    "category": "other",
                    "priority": "low"
                }],
                "total_count": len(requirements) if requirements else 1,
                "categories": categories,
                "extracted_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Requirements extraction error: {e}")
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

# ============================================================================
# MERGENLITE CORE ANALYSIS ORCHESTRATOR
# ============================================================================

@dataclass
class AnalysisResult:
    """Analiz sonuçları için veri yapısı"""
    agent_name: str
    status: str
    output: Dict[str, Any]
    processing_time: float
    timestamp: str

class MergenLiteOrchestrator:
    """
    MergenLite Çekirdek Analiz Orkestratörü
    Database-First yaklaşım ile 4 ajanı sırayla çalıştırır
    """
    
    def __init__(self):
        self.agents = {
            "document_processor": DocumentProcessorAgent(),
            "requirements_extractor": RequirementsExtractorAgent(),
            "compliance_analyst": ComplianceAnalystAgent(),
            "proposal_writer": ProposalWriterAgent()
        }
        
    def run_full_analysis(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tam analiz akışını çalıştır - Database-First için tek JSON çıktısı
        """
        notice_id = opportunity_data.get('noticeId', 'unknown')
        logger.info(f"🤖 MergenLite çekirdek analiz başlatıldı: {notice_id}")
        
        analysis_results = []
        start_time = datetime.now()
        
        # Adım 1: Document Processing
        try:
            step_start = datetime.now()
            
            # Document processor kullan
            if process_documents_for_opportunity:
                doc_result = process_documents_for_opportunity(opportunity_data)
            else:
                # Fallback mock data
                doc_result = {
                    "notice_id": notice_id,
                    "processing_status": "completed",
                    "consolidated_text": "Mock solicitation document content...",
                    "total_word_count": 1000,
                    "document_count": 2
                }
            
            step_end = datetime.now()
            analysis_results.append(AnalysisResult(
                agent_name="document_processor",
                status="completed",
                output=doc_result,
                processing_time=(step_end - step_start).total_seconds(),
                timestamp=step_end.isoformat()
            ))
            logger.info("✅ Document Processing tamamlandı")
        except Exception as e:
            logger.error(f"❌ Document Processing hatası: {e}")
            analysis_results.append(AnalysisResult(
                agent_name="document_processor",
                status="failed",
                output={"error": str(e)},
                processing_time=0,
                timestamp=datetime.now().isoformat()
            ))
        
        # Adım 2: Requirements Extraction
        try:
            step_start = datetime.now()
            consolidated_text = analysis_results[0].output.get('consolidated_text', '') if analysis_results else ''
            
            requirements_result = self.agents["requirements_extractor"].extract_requirements(
                consolidated_text, opportunity_data
            )
            
            step_end = datetime.now()
            analysis_results.append(AnalysisResult(
                agent_name="requirements_extractor",
                status="completed",
                output=requirements_result,
                processing_time=(step_end - step_start).total_seconds(),
                timestamp=step_end.isoformat()
            ))
            logger.info("✅ Requirements Extraction tamamlandı")
        except Exception as e:
            logger.error(f"❌ Requirements Extraction hatası: {e}")
            analysis_results.append(AnalysisResult(
                agent_name="requirements_extractor",
                status="failed",
                output={"error": str(e)},
                processing_time=0,
                timestamp=datetime.now().isoformat()
            ))
        
        # Adım 3: Compliance Analysis
        try:
            step_start = datetime.now()
            requirements = [r.output for r in analysis_results if r.agent_name == "requirements_extractor" and r.status == "completed"]
            requirements_data = requirements[0] if requirements else {}
            
            compliance_result = self.agents["compliance_analyst"].analyze_compliance(
                requirements_data.get('requirements', []), {}
            )
            
            step_end = datetime.now()
            analysis_results.append(AnalysisResult(
                agent_name="compliance_analyst",
                status="completed",
                output=compliance_result,
                processing_time=(step_end - step_start).total_seconds(),
                timestamp=step_end.isoformat()
            ))
            logger.info("✅ Compliance Analysis tamamlandı")
        except Exception as e:
            logger.error(f"❌ Compliance Analysis hatası: {e}")
            analysis_results.append(AnalysisResult(
                agent_name="compliance_analyst",
                status="failed",
                output={"error": str(e)},
                processing_time=0,
                timestamp=datetime.now().isoformat()
            ))
        
        # Adım 4: Proposal Writing
        try:
            step_start = datetime.now()
            successful_results = {r.agent_name: r.output for r in analysis_results if r.status == "completed"}
            
            proposal_result = self.agents["proposal_writer"].write_proposal(
                successful_results, {"opportunity_id": notice_id}
            )
            
            step_end = datetime.now()
            analysis_results.append(AnalysisResult(
                agent_name="proposal_writer",
                status="completed",
                output=proposal_result,
                processing_time=(step_end - step_start).total_seconds(),
                timestamp=step_end.isoformat()
            ))
            logger.info("✅ Proposal Writing tamamlandı")
        except Exception as e:
            logger.error(f"❌ Proposal Writing hatası: {e}")
            analysis_results.append(AnalysisResult(
                agent_name="proposal_writer",
                status="failed",
                output={"error": str(e)},
                processing_time=0,
                timestamp=datetime.now().isoformat()
            ))
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Database-First için konsolide çıktı
        consolidated_output = {
            "notice_id": notice_id,
            "analysis_status": "completed",
            "processed_at": end_time.isoformat(),
            "total_processing_time": total_time,
            "agents_results": {
                result.agent_name: {
                    "status": result.status,
                    "output": result.output,
                    "processing_time": result.processing_time,
                    "timestamp": result.timestamp
                } for result in analysis_results
            },
            "summary": {
                "total_agents": len(analysis_results),
                "successful_agents": len([r for r in analysis_results if r.status == "completed"]),
                "failed_agents": len([r for r in analysis_results if r.status == "failed"]),
                "overall_score": self._calculate_overall_score(analysis_results)
            },
            "metadata": {
                "orchestrator_version": "1.0",
                "mergenlite_core": True,
                "database_first": True
            }
        }
        
        logger.info(f"✅ MergenLite çekirdek analiz tamamlandı: {notice_id} - {consolidated_output['summary']['successful_agents']}/{consolidated_output['summary']['total_agents']} ajan başarılı")
        return consolidated_output
    
    def _calculate_overall_score(self, results: List[AnalysisResult]) -> str:
        """
        Genel analiz skorunu hesapla
        """
        successful = len([r for r in results if r.status == "completed"])
        total = len(results)
        
        if successful == total:
            return "Mükemmel"
        elif successful >= total * 0.75:
            return "İyi"
        elif successful >= total * 0.5:
            return "Orta"
        else:
            return "Zayıf"

# Convenience function for external use
def run_mergenlite_analysis(opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    MergenLite çekirdek analiz - dış modüllerden kullanım için
    """
    orchestrator = MergenLiteOrchestrator()
    return orchestrator.run_full_analysis(opportunity_data)


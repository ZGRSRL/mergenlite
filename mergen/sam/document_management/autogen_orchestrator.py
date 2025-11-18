"""
AutoGen Orchestrator - Multi-Agent Analysis System
Coordinates multiple AutoGen agents for comprehensive opportunity analysis
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# AutoGen imports (optional)
try:
    from autogen import ConversableAgent, GroupChat, GroupChatManager
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logger.warning("AutoGen not available, using fallback analysis")

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Analysis result data structure"""
    opportunity_id: str
    go_no_go_score: float
    risks: List[Dict[str, Any]]
    requirements: List[Dict[str, Any]]
    missing_items: List[str]
    summary: str
    action_items: List[str]
    qa_pairs: List[Dict[str, str]]
    analysis_timestamp: str
    confidence: float

class SAMOpportunityAgent:
    """Agent for fetching and preparing opportunity data"""
    
    def __init__(self):
        self.name = "SAMOpportunityAgent"
        self.agent = None
        
        if AUTOGEN_AVAILABLE:
            try:
                self.agent = ConversableAgent(
                    name=self.name,
                    system_message="""You are a SAM.gov opportunity specialist. Your role is to:
1. Fetch opportunity metadata from SAM.gov
2. Extract key information: title, description, deadline, requirements
3. Identify attachment URLs and types
4. Prepare structured data for analysis

Return data in JSON format with fields: title, description, deadline, requirements, attachments, key_info.""",
                    llm_config={
                        "model": "gpt-4",
                        "temperature": 0.1,
                        "max_tokens": 2000
                    }
                )
            except Exception as e:
                logger.warning(f"SAMOpportunityAgent initialization failed: {e}")
                self.agent = None
    
    def fetch_opportunity_data(self, notice_id: str, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch and structure opportunity data"""
        try:
            if self.agent:
                prompt = f"""
                Analyze this SAM.gov opportunity data and extract key information:
                
                Notice ID: {notice_id}
                Raw Data: {json.dumps(opportunity_data, indent=2)}
                
                Extract and structure:
                1. Title and description
                2. Deadline/due date
                3. Key requirements
                4. Attachment information
                5. Evaluation criteria
                6. Scope of work
                
                Return structured JSON.
                """
                
                response = self.agent.generate_reply(
                    messages=[{"role": "user", "content": prompt}]
                )
                
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return self._fallback_extraction(opportunity_data)
            else:
                return self._fallback_extraction(opportunity_data)
                
        except Exception as e:
            logger.error(f"SAMOpportunityAgent failed: {e}")
            return self._fallback_extraction(opportunity_data)
    
    def _fallback_extraction(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback extraction without AutoGen"""
        return {
            "title": opportunity_data.get("title", "Unknown"),
            "description": opportunity_data.get("description", ""),
            "deadline": opportunity_data.get("responseDeadLine", ""),
            "requirements": [],
            "attachments": opportunity_data.get("resourceLinks", []),
            "key_info": {
                "agency": opportunity_data.get("department", ""),
                "naics": opportunity_data.get("naicsCode", ""),
                "set_aside": opportunity_data.get("typeOfSetAside", "")
            }
        }

class DocumentAnalysisAgent:
    """Agent for analyzing document chunks"""
    
    def __init__(self):
        self.name = "DocumentAnalysisAgent"
        self.agent = None
        
        if AUTOGEN_AVAILABLE:
            try:
                self.agent = ConversableAgent(
                    name=self.name,
                    system_message="""You are a document analysis specialist. Your role is to:
1. Analyze document chunks for mandatory requirements
2. Extract scope of work details
3. Identify evaluation criteria
4. Find submission instructions and deadlines
5. Extract key terms and conditions

For each chunk, return findings in JSON format:
{
    "chunk_id": "chunk_identifier",
    "findings": [
        {
            "type": "requirement|scope|evaluation|deadline|instruction",
            "content": "extracted text",
            "importance": "high|medium|low",
            "category": "mandatory|nice_to_have|optional"
        }
    ]
}""",
                    llm_config={
                        "model": "gpt-4",
                        "temperature": 0.2,
                        "max_tokens": 3000
                    }
                )
            except Exception as e:
                logger.warning(f"DocumentAnalysisAgent initialization failed: {e}")
                self.agent = None
    
    def analyze_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a document chunk"""
        try:
            if self.agent:
                prompt = f"""
                Analyze this document chunk for procurement requirements:
                
                Chunk ID: {chunk.get('chunk_idx', 'unknown')}
                Text: {chunk.get('text', '')[:2000]}  # Limit text length
                
                Extract:
                1. Mandatory requirements
                2. Scope of work
                3. Evaluation criteria
                4. Deadlines
                5. Submission instructions
                
                Return findings in JSON format.
                """
                
                response = self.agent.generate_reply(
                    messages=[{"role": "user", "content": prompt}]
                )
                
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return self._fallback_chunk_analysis(chunk)
            else:
                return self._fallback_chunk_analysis(chunk)
                
        except Exception as e:
            logger.error(f"DocumentAnalysisAgent failed: {e}")
            return self._fallback_chunk_analysis(chunk)
    
    def _fallback_chunk_analysis(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback chunk analysis"""
        text = chunk.get('text', '').lower()
        
        findings = []
        
        # Simple keyword-based analysis
        if any(word in text for word in ['requirement', 'mandatory', 'must']):
            findings.append({
                "type": "requirement",
                "content": "Requirements mentioned",
                "importance": "high",
                "category": "mandatory"
            })
        
        if any(word in text for word in ['deadline', 'due date', 'submission']):
            findings.append({
                "type": "deadline",
                "content": "Deadline information found",
                "importance": "high",
                "category": "mandatory"
            })
        
        return {
            "chunk_id": chunk.get('chunk_idx', 'unknown'),
            "findings": findings
        }

class AIAnalysisAgent:
    """Agent for scoring and risk analysis"""
    
    def __init__(self):
        self.name = "AIAnalysisAgent"
        self.agent = None
        
        if AUTOGEN_AVAILABLE:
            try:
                self.agent = ConversableAgent(
                    name=self.name,
                    system_message="""You are a procurement analysis specialist. Your role is to:
1. Analyze opportunity data and document findings
2. Calculate go/no-go score (0-100)
3. Identify risks and their levels
4. Categorize requirements (mandatory/nice-to-have)
5. Identify missing information

Return analysis in JSON format:
{
    "go_no_go_score": 85,
    "confidence": 0.8,
    "risks": [
        {
            "type": "technical|financial|timeline|compliance",
            "level": "high|medium|low",
            "description": "risk description",
            "mitigation": "suggested mitigation"
        }
    ],
    "requirements": [
        {
            "type": "mandatory|nice_to_have|optional",
            "description": "requirement description",
            "criticality": "high|medium|low"
        }
    ],
    "missing_items": ["list of missing information"]
}""",
                    llm_config={
                        "model": "gpt-4",
                        "temperature": 0.3,
                        "max_tokens": 2000
                    }
                )
            except Exception as e:
                logger.warning(f"AIAnalysisAgent initialization failed: {e}")
                self.agent = None
    
    def analyze_opportunity(self, opportunity_data: Dict[str, Any], document_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze opportunity and provide scoring"""
        try:
            if self.agent:
                prompt = f"""
                Analyze this procurement opportunity:
                
                Opportunity Data: {json.dumps(opportunity_data, indent=2)}
                
                Document Findings: {json.dumps(document_findings, indent=2)}
                
                Provide:
                1. Go/No-Go score (0-100)
                2. Risk analysis
                3. Requirement categorization
                4. Missing information
                
                Return analysis in JSON format.
                """
                
                response = self.agent.generate_reply(
                    messages=[{"role": "user", "content": prompt}]
                )
                
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return self._fallback_analysis(opportunity_data, document_findings)
            else:
                return self._fallback_analysis(opportunity_data, document_findings)
                
        except Exception as e:
            logger.error(f"AIAnalysisAgent failed: {e}")
            return self._fallback_analysis(opportunity_data, document_findings)
    
    def _fallback_analysis(self, opportunity_data: Dict[str, Any], document_findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback analysis without AutoGen"""
        # Simple scoring based on available data
        score = 50  # Base score
        
        if opportunity_data.get("title"):
            score += 10
        if opportunity_data.get("description"):
            score += 10
        if document_findings:
            score += 20
        
        return {
            "go_no_go_score": min(score, 100),
            "confidence": 0.6,
            "risks": [
                {
                    "type": "information",
                    "level": "medium",
                    "description": "Limited information available",
                    "mitigation": "Request additional details"
                }
            ],
            "requirements": [],
            "missing_items": ["Detailed requirements", "Evaluation criteria"]
        }

class SummaryAgent:
    """Agent for generating executive summary"""
    
    def __init__(self):
        self.name = "SummaryAgent"
        self.agent = None
        
        if AUTOGEN_AVAILABLE:
            try:
                self.agent = ConversableAgent(
                    name=self.name,
                    system_message="""You are an executive summary specialist. Your role is to:
1. Create concise executive summary (1-2 paragraphs)
2. Generate action items (6 key points)
3. Create Q&A pairs for common questions

Return summary in JSON format:
{
    "executive_summary": "1-2 paragraph summary",
    "action_items": ["6 key action points"],
    "qa_pairs": [
        {
            "question": "common question",
            "answer": "concise answer"
        }
    ]
}""",
                    llm_config={
                        "model": "gpt-4",
                        "temperature": 0.4,
                        "max_tokens": 1500
                    }
                )
            except Exception as e:
                logger.warning(f"SummaryAgent initialization failed: {e}")
                self.agent = None
    
    def generate_summary(self, opportunity_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary"""
        try:
            if self.agent:
                prompt = f"""
                Create an executive summary for this procurement analysis:
                
                Opportunity: {json.dumps(opportunity_data, indent=2)}
                Analysis: {json.dumps(analysis_result, indent=2)}
                
                Generate:
                1. Executive summary (1-2 paragraphs)
                2. 6 key action items
                3. Q&A pairs for common questions
                
                Return in JSON format.
                """
                
                response = self.agent.generate_reply(
                    messages=[{"role": "user", "content": prompt}]
                )
                
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    return self._fallback_summary(opportunity_data, analysis_result)
            else:
                return self._fallback_summary(opportunity_data, analysis_result)
                
        except Exception as e:
            logger.error(f"SummaryAgent failed: {e}")
            return self._fallback_summary(opportunity_data, analysis_result)
    
    def _fallback_summary(self, opportunity_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback summary generation"""
        title = opportunity_data.get("title", "Unknown Opportunity")
        score = analysis_result.get("go_no_go_score", 0)
        
        return {
            "executive_summary": f"This opportunity '{title}' has been analyzed with a go/no-go score of {score}/100. The analysis indicates {'favorable' if score > 70 else 'mixed' if score > 50 else 'unfavorable'} conditions for pursuit.",
            "action_items": [
                "Review opportunity requirements",
                "Assess technical capabilities",
                "Evaluate resource requirements",
                "Check compliance requirements",
                "Prepare proposal strategy",
                "Monitor deadline closely"
            ],
            "qa_pairs": [
                {
                    "question": "What is the go/no-go score?",
                    "answer": f"The analysis shows a score of {score}/100"
                },
                {
                    "question": "What are the main risks?",
                    "answer": "Review the risk analysis section for detailed information"
                }
            ]
        }

class AutoGenOrchestrator:
    """Main orchestrator for multi-agent analysis"""
    
    def __init__(self):
        self.sam_agent = SAMOpportunityAgent()
        self.doc_agent = DocumentAnalysisAgent()
        self.ai_agent = AIAnalysisAgent()
        self.summary_agent = SummaryAgent()
        
        logger.info("AutoGen Orchestrator initialized")
    
    def run_full_analysis(self, notice_id: str, opportunity_data: Dict[str, Any], document_chunks: List[Dict[str, Any]]) -> AnalysisResult:
        """Run complete analysis pipeline"""
        try:
            logger.info(f"Starting full analysis for: {notice_id}")
            
            # Step 1: SAM Opportunity Agent
            logger.info("Step 1: SAM Opportunity Analysis")
            opportunity_analysis = self.sam_agent.fetch_opportunity_data(notice_id, opportunity_data)
            
            # Step 2: Document Analysis Agent
            logger.info("Step 2: Document Analysis")
            document_findings = []
            for chunk in document_chunks:
                chunk_analysis = self.doc_agent.analyze_chunk(chunk)
                document_findings.append(chunk_analysis)
            
            # Step 3: AI Analysis Agent
            logger.info("Step 3: AI Analysis")
            analysis_result = self.ai_agent.analyze_opportunity(opportunity_analysis, document_findings)
            
            # Step 4: Summary Agent
            logger.info("Step 4: Summary Generation")
            summary_result = self.summary_agent.generate_summary(opportunity_analysis, analysis_result)
            
            # Create final result
            result = AnalysisResult(
                opportunity_id=notice_id,
                go_no_go_score=analysis_result.get("go_no_go_score", 0),
                risks=analysis_result.get("risks", []),
                requirements=analysis_result.get("requirements", []),
                missing_items=analysis_result.get("missing_items", []),
                summary=summary_result.get("executive_summary", ""),
                action_items=summary_result.get("action_items", []),
                qa_pairs=summary_result.get("qa_pairs", []),
                analysis_timestamp=datetime.now().isoformat(),
                confidence=analysis_result.get("confidence", 0.0)
            )
            
            logger.info(f"Analysis completed for: {notice_id}")
            return result
            
        except Exception as e:
            logger.error(f"Full analysis failed for {notice_id}: {e}")
            # Return error result
            return AnalysisResult(
                opportunity_id=notice_id,
                go_no_go_score=0,
                risks=[{"type": "system", "level": "high", "description": str(e), "mitigation": "Check system logs"}],
                requirements=[],
                missing_items=[],
                summary=f"Analysis failed: {e}",
                action_items=["Review error logs", "Retry analysis"],
                qa_pairs=[],
                analysis_timestamp=datetime.now().isoformat(),
                confidence=0.0
            )

# Global instance
orchestrator = AutoGenOrchestrator()

def run_full_analysis(notice_id: str, opportunity_data: Dict[str, Any], document_chunks: List[Dict[str, Any]]) -> AnalysisResult:
    """Run complete analysis pipeline"""
    return orchestrator.run_full_analysis(notice_id, opportunity_data, document_chunks)

if __name__ == "__main__":
    # Test the orchestrator
    print("AutoGen Orchestrator Test")
    
    # Mock data for testing
    test_opportunity = {
        "title": "Test Opportunity",
        "description": "Test description",
        "noticeId": "TEST123"
    }
    
    test_chunks = [
        {"chunk_idx": 0, "text": "This is a test chunk with requirements and deadlines."}
    ]
    
    result = run_full_analysis("TEST123", test_opportunity, test_chunks)
    print(f"Analysis result: {result}")


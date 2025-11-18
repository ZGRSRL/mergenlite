"""
AutoGen Analysis Center Module
Advanced AI analysis capabilities for SAM.gov opportunities
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from autogen_agents import (
    SAMOpportunityAgent,
    DocumentAnalysisAgent,
    ProposalAgent,
    AIAnalysisAgent,
    SummaryAgent,
    CoordinatorAgent
)

logger = logging.getLogger(__name__)

class AutoGenAnalysisCenter:
    """AutoGen Analysis Center for comprehensive opportunity analysis"""
    
    def __init__(self):
        self.sam_agent = SAMOpportunityAgent()
        self.doc_agent = DocumentAnalysisAgent()
        self.proposal_agent = ProposalAgent()
        self.ai_agent = AIAnalysisAgent()
        self.summary_agent = SummaryAgent()
        self.coordinator = CoordinatorAgent()
        
        logger.info("AutoGen Analysis Center initialized")
    
    def analyze_opportunity_comprehensive(self, opportunity_id: str) -> Dict[str, Any]:
        """Comprehensive opportunity analysis"""
        try:
            logger.info(f"Comprehensive analysis started for: {opportunity_id}")
            
            # 1. Opportunity analysis
            opp_analysis = self.ai_agent.analyze_opportunity(opportunity_id)
            
            # 2. Document analysis
            doc_analysis = self.doc_agent.analyze_documents(opportunity_id)
            
            # 3. Proposal drafting
            proposal = self.proposal_agent.generate_proposal_outline(opportunity_id)
            
            # 4. Combine results
            comprehensive_result = {
                'opportunity_id': opportunity_id,
                'analysis_timestamp': datetime.now().isoformat(),
                'opportunity_analysis': opp_analysis,
                'document_analysis': doc_analysis,
                'proposal_draft': proposal,
                'summary': {
                    'total_documents': len(doc_analysis.get('documents', [])),
                    'analysis_confidence': opp_analysis.get('confidence', 0.0),
                    'proposal_status': proposal.get('status', 'unknown')
                }
            }
            
            logger.info(f"Comprehensive analysis completed for: {opportunity_id}")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed for {opportunity_id}: {e}")
            return {
                'opportunity_id': opportunity_id,
                'error': str(e),
                'analysis_timestamp': datetime.now().isoformat()
            }
    
    def batch_analyze_opportunities(self, opportunity_ids: List[str]) -> Dict[str, Any]:
        """Batch analysis of multiple opportunities"""
        try:
            logger.info(f"Batch analysis started for {len(opportunity_ids)} opportunities")
            
            results = []
            successful = 0
            failed = 0
            
            for opp_id in opportunity_ids:
                try:
                    result = self.analyze_opportunity_comprehensive(opp_id)
                    results.append(result)
                    
                    if 'error' not in result:
                        successful += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Batch analysis failed for {opp_id}: {e}")
                    results.append({
                        'opportunity_id': opp_id,
                        'error': str(e),
                        'analysis_timestamp': datetime.now().isoformat()
                    })
                    failed += 1
            
            batch_result = {
                'total_opportunities': len(opportunity_ids),
                'successful': successful,
                'failed': failed,
                'results': results,
                'batch_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Batch analysis completed: {successful} successful, {failed} failed")
            return batch_result
            
        except Exception as e:
            logger.error(f"Batch analysis failed: {e}")
            return {
                'error': str(e),
                'batch_timestamp': datetime.now().isoformat()
            }
    
    def generate_analysis_report(self, analysis_results: Dict[str, Any]) -> str:
        """Generate human-readable analysis report"""
        try:
            report = f"""
# AutoGen Analysis Report

**Analysis Date:** {analysis_results.get('analysis_timestamp', 'Unknown')}
**Opportunity ID:** {analysis_results.get('opportunity_id', 'Unknown')}

## Opportunity Analysis
"""
            
            opp_analysis = analysis_results.get('opportunity_analysis', {})
            if opp_analysis:
                report += f"""
- **Confidence Score:** {opp_analysis.get('confidence', 0.0):.2%}
- **Key Requirements:** {', '.join(opp_analysis.get('key_requirements', []))}
- **Risk Level:** {opp_analysis.get('risk_level', 'Unknown')}
- **Estimated Value:** {opp_analysis.get('estimated_value', 'Unknown')}
"""
            
            doc_analysis = analysis_results.get('document_analysis', {})
            if doc_analysis:
                report += f"""
## Document Analysis
- **Total Documents:** {len(doc_analysis.get('documents', []))}
- **Analysis Status:** {doc_analysis.get('status', 'Unknown')}
"""
                
                documents = doc_analysis.get('documents', [])
                for i, doc in enumerate(documents, 1):
                    report += f"""
### Document {i}
- **Type:** {doc.get('type', 'Unknown')}
- **Analysis:** {doc.get('analysis', 'No analysis available')}
"""
            
            proposal = analysis_results.get('proposal_draft', {})
            if proposal:
                report += f"""
## Proposal Draft
- **Status:** {proposal.get('status', 'Unknown')}
- **Draft Available:** {'Yes' if proposal.get('draft') else 'No'}
"""
            
            summary = analysis_results.get('summary', {})
            if summary:
                report += f"""
## Summary
- **Total Documents Analyzed:** {summary.get('total_documents', 0)}
- **Analysis Confidence:** {summary.get('analysis_confidence', 0.0):.2%}
- **Proposal Status:** {summary.get('proposal_status', 'Unknown')}
"""
            
            return report
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return f"Error generating report: {e}"
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get analysis center statistics"""
        try:
            # This would typically query a database for statistics
            # For now, return mock data
            return {
                'total_analyses': 0,
                'successful_analyses': 0,
                'failed_analyses': 0,
                'average_confidence': 0.0,
                'last_analysis': None,
                'most_analyzed_opportunity_type': 'Unknown'
            }
        except Exception as e:
            logger.error(f"Statistics retrieval failed: {e}")
            return {'error': str(e)}

# Global instance
analysis_center = AutoGenAnalysisCenter()

def analyze_opportunity_comprehensive(opportunity_id: str) -> Dict[str, Any]:
    """Comprehensive opportunity analysis"""
    return analysis_center.analyze_opportunity_comprehensive(opportunity_id)

def batch_analyze_opportunities(opportunity_ids: List[str]) -> Dict[str, Any]:
    """Batch analysis of multiple opportunities"""
    return analysis_center.batch_analyze_opportunities(opportunity_ids)

def generate_analysis_report(analysis_results: Dict[str, Any]) -> str:
    """Generate human-readable analysis report"""
    return analysis_center.generate_analysis_report(analysis_results)

def get_analysis_statistics() -> Dict[str, Any]:
    """Get analysis center statistics"""
    return analysis_center.get_analysis_statistics()

if __name__ == "__main__":
    # Test the analysis center
    print("AutoGen Analysis Center Test")
    
    # Test comprehensive analysis
    test_opp_id = "test_opportunity_123"
    result = analyze_opportunity_comprehensive(test_opp_id)
    print(f"Analysis result: {result}")
    
    # Test report generation
    report = generate_analysis_report(result)
    print(f"Generated report:\n{report}")
    
    # Test statistics
    stats = get_analysis_statistics()
    print(f"Statistics: {stats}")


"""
Start a SOW analysis for an opportunity
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal
from app.models import Opportunity
from app.services.pipeline_service import create_pipeline_job, run_pipeline_job
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_analysis(opportunity_id: int = None, analysis_type: str = "sow_draft"):
    """Start a pipeline analysis for an opportunity"""
    db = SessionLocal()
    try:
        # Get opportunity
        if opportunity_id:
            opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        else:
            # Get latest opportunity
            opportunity = db.query(Opportunity).order_by(Opportunity.created_at.desc()).first()
        
        if not opportunity:
            logger.error("No opportunity found")
            return None
        
        logger.info(f"Starting {analysis_type} analysis for opportunity {opportunity.id} ({opportunity.notice_id or opportunity.title})")
        
        # Create pipeline job
        analysis_result, agent_run_id = create_pipeline_job(
            db=db,
            opportunity_id=opportunity.id,
            analysis_type=analysis_type,
            pipeline_version="v1",
            agent_name="autogen",
            initial_options={},
        )
        
        logger.info(f"Created pipeline job: {analysis_result.id}")
        
        # Prepare payload
        payload = {
            "opportunity_id": opportunity.id,
            "analysis_type": analysis_type,
            "pipeline_version": "v1",
            "agent_name": "autogen",
            "options": {},
            "agent_run_id": agent_run_id,
        }
        
        # Run pipeline job (synchronous for testing)
        logger.info(f"Running pipeline job {analysis_result.id}...")
        run_pipeline_job(analysis_result.id, payload)
        
        logger.info(f"Pipeline job {analysis_result.id} completed")
        
        # Refresh to get latest status
        db.refresh(analysis_result)
        logger.info(f"Final status: {analysis_result.status}")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"Error starting analysis: {e}", exc_info=True)
        return None
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Start a pipeline analysis")
    parser.add_argument("--opportunity-id", type=int, help="Opportunity ID (default: latest)")
    parser.add_argument("--analysis-type", type=str, default="sow_draft", choices=["sow_draft", "sow", "hotel_match"], help="Analysis type")
    
    args = parser.parse_args()
    
    result = start_analysis(
        opportunity_id=args.opportunity_id,
        analysis_type=args.analysis_type
    )
    
    if result:
        print(f"\n✅ Analysis started successfully!")
        print(f"   Analysis ID: {result.id}")
        print(f"   Status: {result.status}")
        print(f"   Opportunity ID: {result.opportunity_id}")
        if result.pdf_path:
            print(f"   PDF: {result.pdf_path}")
        if result.json_path:
            print(f"   JSON: {result.json_path}")
    else:
        print("\nFailed to start analysis")


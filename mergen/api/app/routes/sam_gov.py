"""
SAM.gov API Routes
Endpoints for SAM.gov integration
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..db import get_db
from ..services.sam_gov.integration import (
    SAMGovIntegration, 
    fetch_sam_gov_opportunities,
    SAM_GOV_CONFIGS
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/search")
async def search_sam_opportunities(
    keywords: List[str] = None,
    naics_codes: List[str] = None,
    date_range_days: int = 30,
    opportunity_type: str = "rfq",
    max_results: int = 50
):
    """Search for opportunities on SAM.gov"""
    
    try:
        sam_integration = SAMGovIntegration()
        
        opportunities = await sam_integration.search_opportunities(
            keywords=keywords,
            naics_codes=naics_codes,
            date_range_days=date_range_days,
            opportunity_type=opportunity_type
        )
        
        # Limit results
        opportunities = opportunities[:max_results]
        
        return {
            "status": "success",
            "count": len(opportunities),
            "opportunities": opportunities
        }
        
    except Exception as e:
        logger.error(f"Error searching SAM.gov opportunities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch")
async def fetch_opportunities(
    background_tasks: BackgroundTasks,
    config_name: str = "conference_meetings",
    max_opportunities: int = 10,
    db: Session = Depends(get_db)
):
    """Fetch and process opportunities from SAM.gov"""
    
    try:
        # Validate config name
        if config_name not in SAM_GOV_CONFIGS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid config name. Available: {list(SAM_GOV_CONFIGS.keys())}"
            )
        
        # Start background task
        background_tasks.add_task(
            _process_sam_opportunities,
            config_name,
            max_opportunities
        )
        
        return {
            "status": "started",
            "message": f"Started fetching {max_opportunities} opportunities using {config_name} config",
            "config": SAM_GOV_CONFIGS[config_name]
        }
        
    except Exception as e:
        logger.error(f"Error starting SAM.gov fetch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configs")
async def get_sam_configs():
    """Get available SAM.gov search configurations"""
    
    return {
        "configs": SAM_GOV_CONFIGS,
        "default": "conference_meetings"
    }

@router.get("/opportunity/{notice_id}")
async def get_opportunity_details(notice_id: str):
    """Get detailed information about a specific opportunity"""
    
    try:
        sam_integration = SAMGovIntegration()
        details = await sam_integration.get_opportunity_details(notice_id)
        
        if not details:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        return {
            "status": "success",
            "opportunity": details
        }
        
    except Exception as e:
        logger.error(f"Error fetching opportunity details: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process/{notice_id}")
async def process_opportunity(
    notice_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Process a specific SAM.gov opportunity"""
    
    try:
        sam_integration = SAMGovIntegration()
        
        # Get opportunity details first
        details = await sam_integration.get_opportunity_details(notice_id)
        if not details:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Process in background
        background_tasks.add_task(
            _process_single_opportunity,
            notice_id,
            details
        )
        
        return {
            "status": "started",
            "message": f"Started processing opportunity {notice_id}",
            "title": details.get("title", "Unknown")
        }
        
    except Exception as e:
        logger.error(f"Error processing opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_sam_status():
    """Get SAM.gov integration status"""
    
    return {
        "status": "active",
        "api_available": True,
        "configurations": len(SAM_GOV_CONFIGS),
        "supported_types": ["rfq", "rfi", "sources_sought", "sow"]
    }

# Background task functions
async def _process_sam_opportunities(config_name: str, max_opportunities: int):
    """Background task to process SAM.gov opportunities"""
    
    try:
        logger.info(f"Starting SAM.gov opportunity processing with config: {config_name}")
        
        results = await fetch_sam_gov_opportunities(
            config_name=config_name,
            max_opportunities=max_opportunities
        )
        
        logger.info(f"SAM.gov processing completed. Processed {len(results)} opportunities")
        
    except Exception as e:
        logger.error(f"Error in background SAM.gov processing: {e}")

async def _process_single_opportunity(notice_id: str, opportunity_details: Dict[str, Any]):
    """Background task to process a single opportunity"""
    
    try:
        logger.info(f"Processing single opportunity: {notice_id}")
        
        sam_integration = SAMGovIntegration()
        db_session = next(get_db())
        
        try:
            result = await sam_integration.process_sam_opportunity(
                opportunity_details, 
                db_session
            )
            logger.info(f"Opportunity {notice_id} processed successfully")
            
        finally:
            db_session.close()
            
    except Exception as e:
        logger.error(f"Error processing single opportunity {notice_id}: {e}")



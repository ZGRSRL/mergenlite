"""
Opportunities API Routes
SAM.gov opportunity management endpoints
"""
import os
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Load .env file from mergen/.env
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent.parent.parent.parent
    mergen_env_path = project_root / "mergen" / ".env"
    
    if mergen_env_path.exists():
        load_dotenv(mergen_env_path, override=True)
        print(f"[opportunities.py] Loaded .env from: {mergen_env_path}")
    else:
        alt_paths = [
            project_root / ".env",
            Path("mergen/.env"),
            Path(".env"),
        ]
        for alt_path in alt_paths:
            if alt_path.exists():
                load_dotenv(alt_path, override=True)
                print(f"[opportunities.py] Loaded .env from: {alt_path}")
                break
        else:
            print(f"[opportunities.py] .env file not found. Tried: {mergen_env_path}")
except ImportError:
    print("[opportunities.py] python-dotenv not installed")
except Exception as e:
    print(f"[opportunities.py] Error loading .env: {e}")

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ..db import get_db
from ..models import (
    Opportunity,
    OpportunityAttachment,
    SyncJob,
    SyncLog,
    DownloadJob,
    DownloadLog,
    OpportunityHistory,
    AgentRun,
    TrainingExample,
    DecisionCache,
    EmailLog,
    AIAnalysisResult,
)
from ..schemas import (
    OpportunityRead,
    OpportunityWithAttachments,
    OpportunityAttachmentRead,
    SyncResponse,
    SyncJobRead,
    SyncLogRead,
    DownloadResponse,
    DownloadJobRead,
    DownloadLogRead,
    OpportunityHistoryRead,
    AgentRunRead,
    TrainingExampleRead,
    DecisionCacheRead,
    DecisionCacheContext,
    DecisionCacheLookupResponse,
    DecisionCacheSaveRequest,
    EmailLogRead,
    EmailLogCreate,
    HotelMatchRead,
)
from fastapi import BackgroundTasks, Body
import logging

from ..services.decision_cache_service import (
    lookup_decision_cache as lookup_decision_cache_service,
    persist_decision_cache,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/opportunities", tags=["opportunities"])


@router.get("", response_model=List[OpportunityRead])
async def get_opportunities(
    notice_id: Optional[str] = Query(None, description="Filter by notice ID"),
    naics_code: Optional[str] = Query(None, description="Filter by NAICS code"),
    keyword: Optional[str] = Query(None, description="Search in title/description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    List opportunities with pagination and filters
    """
    try:
        # Use CRUD function for consistency
        from ..crud.opportunities import list_opportunities
        
        # Calculate skip
        skip = (page - 1) * page_size
        
        # Parse date filters if needed (for future use)
        date_from = None
        date_to = None
        
        # Get opportunities
        opportunities = list_opportunities(
            db=db,
            skip=skip,
            limit=page_size,
            naics_code=naics_code,
            keyword=keyword,
            date_from=date_from,
            date_to=date_to
        )
        
        # Filter by notice_id if provided
        if notice_id:
            opportunities = [opp for opp in opportunities if notice_id.lower() in (opp.notice_id or "").lower()]
        
        # Pydantic response_model handles serialization automatically
        return opportunities
        
    except Exception as e:
        logger.error(f"Error listing opportunities: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing opportunities: {str(e)}")


@router.get("/{opportunity_id}", response_model=OpportunityWithAttachments)
async def get_opportunity(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    """
    Get opportunity by database ID with attachments
    """
    try:
        from ..crud.opportunities import get_opportunity
        
        opportunity = get_opportunity(db, opportunity_id)
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Pydantic response_model automatically includes attachments via relationship
        return opportunity
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting opportunity {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting opportunity: {str(e)}")


@router.get("/{opportunity_id}/attachments", response_model=List[OpportunityAttachmentRead])
async def get_opportunity_attachments(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all attachments for an opportunity
    """
    try:
        from ..crud.opportunities import get_attachments_for_opportunity

        attachments = get_attachments_for_opportunity(db, opportunity_id)
        return attachments
    except Exception as e:
        logger.error(f"Error getting attachments for opportunity {opportunity_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting attachments: {str(e)}")


@router.get("/{opportunity_id}/history", response_model=List[OpportunityHistoryRead])
async def get_opportunity_history(
    opportunity_id: int,
    limit: int = Query(50, ge=1, le=500, description="Max history entries"),
    db: Session = Depends(get_db),
):
    history = (
        db.query(OpportunityHistory)
        .filter(OpportunityHistory.opportunity_id == opportunity_id)
        .order_by(OpportunityHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    return history


@router.get("/{opportunity_id}/agent-runs", response_model=List[AgentRunRead])
async def get_opportunity_agent_runs(
    opportunity_id: int,
    limit: int = Query(20, ge=1, le=200, description="Max agent runs"),
    db: Session = Depends(get_db),
):
    try:
        runs = (
            db.query(AgentRun)
            .filter(AgentRun.opportunity_id == opportunity_id)
            .order_by(AgentRun.started_at.desc())
            .limit(limit)
            .all()
        )
        return runs
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in get_opportunity_agent_runs: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching agent runs: {str(e)}")


@router.get("/{opportunity_id}/hotel-matches", response_model=List[HotelMatchRead])
async def get_hotel_matches_for_opportunity(
    opportunity_id: int,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    results = (
        db.query(AIAnalysisResult)
        .filter(
            AIAnalysisResult.opportunity_id == opportunity_id,
            AIAnalysisResult.analysis_type == "hotel_match",
        )
        .order_by(AIAnalysisResult.created_at.desc())
        .limit(limit)
        .all()
    )
    response: List[HotelMatchRead] = []
    for res in results:
        payload = res.result_json or {}
        response.append(
            HotelMatchRead(
                id=res.id,
                generated_at=res.completed_at or res.created_at,
                hotels=payload.get("hotels", []),
                reasoning=payload.get("reasoning"),
                decision_metadata=payload.get("decision_metadata"),
            )
        )
    return response


@router.get("/{opportunity_id}/training-examples", response_model=List[TrainingExampleRead])
async def get_training_examples_for_opportunity(
    opportunity_id: int,
    limit: int = Query(20, ge=1, le=200, description="Max training examples"),
    db: Session = Depends(get_db),
):
    examples = (
        db.query(TrainingExample)
        .filter(TrainingExample.opportunity_id == opportunity_id)
        .order_by(TrainingExample.created_at.desc())
        .limit(limit)
        .all()
    )
    return examples


@router.get("/decision-cache/{key_hash}", response_model=DecisionCacheRead)
async def get_decision_cache_entry(
    key_hash: str,
    db: Session = Depends(get_db),
):
    entry = db.query(DecisionCache).filter(DecisionCache.key_hash == key_hash).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Pattern not found")
    return entry


@router.get("/{opportunity_id}/emails", response_model=List[EmailLogRead])
async def get_email_logs_for_opportunity(
    opportunity_id: int,
    limit: int = Query(50, ge=1, le=500, description="Max email logs"),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(EmailLog)
        .filter(EmailLog.opportunity_id == opportunity_id)
        .order_by(EmailLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return logs


@router.post("/{opportunity_id}/decision-cache/lookup", response_model=DecisionCacheLookupResponse)
async def lookup_decision_cache_route(
    opportunity_id: int,
    payload: Optional[DecisionCacheContext] = Body(None),
    db: Session = Depends(get_db),
):
    opportunity: Optional[Opportunity] = None
    if opportunity_id > 0:
        opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

    context = payload.model_dump(exclude_none=True) if payload else {}
    notice_id = context.get("notice_id") or (opportunity.notice_id if opportunity else None)
    try:
        key_hash, signature, entry = lookup_decision_cache_service(
            db,
            opportunity=opportunity,
            context=context,
            notice_id=notice_id,
        )
        # Convert DecisionCache model to DecisionCacheRead schema if entry exists
        pattern = None
        if entry:
            from ..schemas import DecisionCacheRead
            pattern = DecisionCacheRead(
                key_hash=entry.key_hash,
                pattern_desc=entry.pattern_desc,
                recommended_hotels=entry.recommended_hotels,
                created_at=entry.created_at,
                extra_metadata=entry.extra_metadata,
            )
        return DecisionCacheLookupResponse(
            key_hash=key_hash,
            signature=signature,
            matched=entry is not None,
            pattern=pattern,
        )
    except Exception as e:
        logger.error(f"Error in decision cache lookup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Decision cache lookup failed: {str(e)}")


@router.post("/{opportunity_id}/decision-cache/save", response_model=DecisionCacheRead)
async def save_decision_cache_route(
    opportunity_id: int,
    payload: DecisionCacheSaveRequest,
    db: Session = Depends(get_db),
):
    opportunity: Optional[Opportunity] = None
    if opportunity_id > 0:
        opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")

    context = payload.model_dump(exclude_none=True)
    notice_id = context.get("notice_id") or (opportunity.notice_id if opportunity else None)
    key_hash, signature, _ = lookup_decision_cache_service(
        db,
        opportunity=opportunity,
        context=context,
        notice_id=notice_id,
    )
    entry = persist_decision_cache(
        db,
        opportunity=opportunity,
        context=context,
        recommended_hotels=payload.recommended_hotels,
        pattern_desc=payload.pattern_desc,
        notice_id=notice_id,
        key_hash=key_hash,
        signature=signature,
    )
    return entry


@router.post("/{opportunity_id}/emails", response_model=EmailLogRead)
async def create_email_log(
    opportunity_id: int,
    payload: EmailLogCreate,
    db: Session = Depends(get_db),
):
    email_log = EmailLog(
        opportunity_id=opportunity_id,
        direction=payload.direction,
        subject=payload.subject,
        from_address=payload.from_address,
        to_address=payload.to_address,
        message_id=payload.message_id,
        in_reply_to=payload.in_reply_to,
        raw_body=payload.raw_body,
        parsed_summary=payload.parsed_summary,
        related_agent_run_id=payload.related_agent_run_id,
        related_llm_call_id=payload.related_llm_call_id,
    )
    db.add(email_log)
    db.commit()
    db.refresh(email_log)
    return email_log


@router.post("/sync", response_model=SyncResponse)
async def sync_opportunities(
    naics: str = Query("721110", description="NAICS code"),
    days_back: int = Query(30, ge=1, le=365, description="Days to look back"),
    limit: int = Query(1000, ge=1, le=10000, description="Max opportunities to fetch"),
    keyword: Optional[str] = Query(None, description="Keyword search"),
    ptype: Optional[str] = Query(None, description="Opportunity type (o=RFQ, k=Combined)"),
    db: Session = Depends(get_db)
):
    """
    Sync opportunities from SAM.gov/GSA API to database
    Uses centralized sync service with job tracking
    Returns: job_id, count_new, count_updated, total_processed, count_attachments
    """
    try:
        # Import sync service
        from ..services.opportunity_sync_service import sync_from_sam
        from ..schemas import SyncResponse
        
        # Prepare params for sync service
        params = {
            "naics": naics,
            "days_back": days_back,
            "limit": limit,
            "keyword": keyword,
        }
        
        # Call centralized sync service (creates job automatically)
        result = await sync_from_sam(db, params)
        
        return SyncResponse(
            success=True,
            job_id=result.get("job_id"),
            count_new=result.get("count_new", 0),
            count_updated=result.get("count_updated", 0),
            total_processed=result.get("total_processed", 0),
            count_attachments=result.get("count_attachments", 0),
            message="Sync completed successfully"
        )
        
    except Exception as e:
        db.rollback()
        logger.error(f"Sync error: {e}", exc_info=True)
        error_msg = f"Sync error: {str(e)}"
        if "SAM_API_KEY" in str(e):
            error_msg += ". Please check mergen/.env file for SAM_API_KEY."
        raise HTTPException(status_code=500, detail=error_msg)


@router.post("/{opportunity_id}/download-attachments", response_model=DownloadResponse)
async def download_attachments_endpoint(
    opportunity_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Download all attachments for an opportunity from SAM.gov
    Runs as background task, returns job_id immediately
    """
    try:
        from ..services.attachment_service import download_attachments_for_opportunity
        from ..schemas import DownloadResponse
        
        # Verify opportunity exists
        opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        # Create job
        import uuid
        job_id = str(uuid.uuid4())
        from ..models import DownloadJob
        job = DownloadJob(
            job_id=job_id,
            opportunity_id=opportunity_id,
            status='pending'
        )
        db.add(job)
        db.commit()
        
        # Add background task
        async def run_download():
            # Create new session for background task
            from ..db import SessionLocal
            bg_db = SessionLocal()
            try:
                await download_attachments_for_opportunity(bg_db, opportunity_id, job_id)
            finally:
                bg_db.close()
        
        background_tasks.add_task(run_download)
        
        logger.info(f"Started background download job {job_id} for opportunity {opportunity_id}")
        
        return DownloadResponse(
            success=True,
            job_id=job_id,
            message="Download started in background"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting download: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error starting download: {str(e)}")


@router.get("/sync/jobs/{job_id}", response_model=SyncJobRead)
async def get_sync_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get sync job status by job_id
    """
    job = db.query(SyncJob).filter(SyncJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/sync/jobs/{job_id}/logs", response_model=List[SyncLogRead])
async def get_sync_job_logs(
    job_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Max logs to return"),
    db: Session = Depends(get_db)
):
    """
    Get logs for a sync job
    """
    # Verify job exists
    job = db.query(SyncJob).filter(SyncJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get logs
    logs = db.query(SyncLog).filter(
        SyncLog.job_id == job_id
    ).order_by(SyncLog.timestamp.desc()).limit(limit).all()
    
    return logs


@router.get("/sync/jobs", response_model=List[SyncJobRead])
async def list_sync_jobs(
    limit: int = Query(20, ge=1, le=100, description="Max jobs to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    List recent sync jobs
    """
    query = db.query(SyncJob)
    
    if status:
        query = query.filter(SyncJob.status == status)
    
    jobs = query.order_by(SyncJob.created_at.desc()).limit(limit).all()
    return jobs


@router.get("/download/jobs/{job_id}", response_model=DownloadJobRead)
async def get_download_job(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get download job status by job_id
    """
    job = db.query(DownloadJob).filter(DownloadJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/download/jobs/{job_id}/logs", response_model=List[DownloadLogRead])
async def get_download_job_logs(
    job_id: str,
    limit: int = Query(100, ge=1, le=1000, description="Max logs to return"),
    db: Session = Depends(get_db)
):
    """
    Get logs for a download job
    """
    # Verify job exists
    job = db.query(DownloadJob).filter(DownloadJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get logs
    logs = db.query(DownloadLog).filter(
        DownloadLog.job_id == job_id
    ).order_by(DownloadLog.timestamp.desc()).limit(limit).all()
    
    return logs


@router.get("/download/jobs", response_model=List[DownloadJobRead])
async def list_download_jobs(
    opportunity_id: Optional[int] = Query(None, description="Filter by opportunity ID"),
    limit: int = Query(20, ge=1, le=100, description="Max jobs to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    """
    List recent download jobs
    """
    query = db.query(DownloadJob)
    
    if opportunity_id:
        query = query.filter(DownloadJob.opportunity_id == opportunity_id)
    
    if status:
        query = query.filter(DownloadJob.status == status)
    
    jobs = query.order_by(DownloadJob.created_at.desc()).limit(limit).all()
    return jobs

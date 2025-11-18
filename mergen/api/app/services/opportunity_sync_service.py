"""
Opportunity Sync Service
SAM.gov'dan fırsatları çekip veritabanına yazan servis
Job tracking ve logging ile
"""
import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from .sam_service import fetch_opportunities_from_sam
from .sam_mapper import map_sam_record_to_opportunity, extract_attachments_from_sam_record
from ..crud.opportunities import upsert_opportunity, create_attachment, get_opportunity_by_notice_id
from ..models import SyncJob, SyncLog

logger = logging.getLogger(__name__)


def _log_sync(
    db: Session,
    job_id: str,
    level: str,
    message: str,
    step: Optional[str] = None,
    extra_metadata: Optional[Dict] = None,
):
    """Helper to log sync events"""
    log = SyncLog(
        job_id=job_id,
        level=level,
        message=message,
        step=step,
        extra_metadata=extra_metadata,
    )
    db.add(log)
    db.commit()


async def sync_from_sam(db: Session, params: Dict[str, Any], job_id: Optional[str] = None) -> Dict[str, Any]:
    """
    SAM'den fırsatları çek, opportunities tablosuna yaz.
    Attachments bilgisini de opportunity_attachments tablosuna kaydet.
    Job tracking ile.
    
    Args:
        db: Database session
        params: SAM API parametreleri (naics, keyword, days_back, limit, etc.)
        job_id: Optional job ID for tracking (if None, creates new job)
    
    Returns:
        Dict with job_id, count_new, count_updated, total_processed, count_attachments
    """
    # Create or get job
    if not job_id:
        job_id = str(uuid.uuid4())
        job = SyncJob(
            job_id=job_id,
            status='pending',
            sync_type='sam',
            params=params
        )
        db.add(job)
        db.commit()
    else:
        job = db.query(SyncJob).filter(SyncJob.job_id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
    
    # Update job status
    job.status = 'running'
    job.started_at = datetime.now()
    db.commit()
    
    _log_sync(db, job_id, 'INFO', f"Starting SAM sync with params: {params}", step='init')
    logger.info(f"[Job {job_id}] Starting SAM sync with params: {params}")
    
    try:
        # Fetch from SAM
        _log_sync(db, job_id, 'INFO', "Fetching opportunities from SAM.gov", step='fetch')
        records = await fetch_opportunities_from_sam(params)
        
        if not records:
            _log_sync(db, job_id, 'WARNING', "No records fetched from SAM", step='fetch')
            logger.warning(f"[Job {job_id}] No records fetched from SAM")
            job.status = 'completed'
            job.completed_at = datetime.now()
            job.total_processed = 0
            db.commit()
            return {
                "job_id": job_id,
                "count_new": 0,
                "count_updated": 0,
                "total_processed": 0,
                "count_attachments": 0
            }
        
        _log_sync(db, job_id, 'INFO', f"Fetched {len(records)} opportunities from SAM", step='fetch', extra_metadata={"count": len(records)})
        
        count_new = 0
        count_updated = 0
        count_attachments = 0
        
        # Process records
        _log_sync(db, job_id, 'INFO', f"Processing {len(records)} opportunities", step='process')
        
        for idx, record in enumerate(records):
            try:
                # Map SAM record to Opportunity format
                opportunity_data = map_sam_record_to_opportunity(record)
                
                # Check if exists (for counting)
                notice_id = opportunity_data.get("notice_id")
                existing = get_opportunity_by_notice_id(db, notice_id) if notice_id else None
                
                # Upsert opportunity
                opportunity = upsert_opportunity(db, opportunity_data)
                
                if existing:
                    count_updated += 1
                else:
                    count_new += 1
                
                # Extract and save attachments
                attachments_data = extract_attachments_from_sam_record(record, opportunity.id)
                
                for att_data in attachments_data:
                    try:
                        # Check if attachment already exists (by source_url)
                        from ..models import OpportunityAttachment
                        existing_att = db.query(OpportunityAttachment).filter(
                            OpportunityAttachment.opportunity_id == opportunity.id,
                            OpportunityAttachment.source_url == att_data.get("source_url")
                        ).first()
                        
                        if not existing_att:
                            create_attachment(db, att_data)
                            count_attachments += 1
                    except Exception as att_error:
                        logger.warning(f"[Job {job_id}] Error creating attachment {att_data.get('name')}: {att_error}")
                        _log_sync(db, job_id, 'WARNING', f"Error creating attachment: {att_error}", step='attachments', extra_metadata={"attachment_name": att_data.get('name')})
                        continue
                
                # Log progress every 10 records
                if (idx + 1) % 10 == 0:
                    _log_sync(db, job_id, 'INFO', f"Processed {idx + 1}/{len(records)} opportunities", step='process', extra_metadata={"progress": idx + 1, "total": len(records)})
            
            except Exception as opp_error:
                notice_id = record.get('noticeId', 'unknown')
                logger.error(f"[Job {job_id}] Error processing opportunity {notice_id}: {opp_error}", exc_info=True)
                _log_sync(db, job_id, 'ERROR', f"Error processing opportunity: {opp_error}", step='process', extra_metadata={"notice_id": notice_id, "error": str(opp_error)})
                continue
        
        # Update job with results
        job.status = 'completed'
        job.completed_at = datetime.now()
        job.count_new = count_new
        job.count_updated = count_updated
        job.count_attachments = count_attachments
        job.total_processed = len(records)
        db.commit()
        
        _log_sync(db, job_id, 'INFO', f"Sync completed: {count_new} new, {count_updated} updated, {count_attachments} attachments", step='complete')
        logger.info(f"[Job {job_id}] Sync completed: {count_new} new, {count_updated} updated, {count_attachments} attachments")
        
        return {
            "job_id": job_id,
            "count_new": count_new,
            "count_updated": count_updated,
            "total_processed": len(records),
            "count_attachments": count_attachments
        }
    
    except Exception as e:
        # Update job with error
        job.status = 'failed'
        job.completed_at = datetime.now()
        job.error_message = str(e)
        db.commit()
        
        _log_sync(db, job_id, 'ERROR', f"Sync failed: {e}", step='error', extra_metadata={"error": str(e)})
        logger.error(f"[Job {job_id}] Sync failed: {e}", exc_info=True)
        raise


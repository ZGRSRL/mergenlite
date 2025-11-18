"""
Attachment Download Service
SAM.gov'dan attachment'ları indirip dosya sistemine kaydeden servis
Job tracking ve background task desteği ile
"""
import os
import logging
import uuid
from typing import List, Optional, Dict, Any
from pathlib import Path
import httpx
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import Opportunity, OpportunityAttachment, DownloadJob, DownloadLog

logger = logging.getLogger(__name__)

# Base data directory
BASE_DATA_DIR = os.getenv("DATA_DIR", "data")


def _log_download(db: Session, job_id: str, level: str, message: str, step: Optional[str] = None, attachment_name: Optional[str] = None, extra_metadata: Optional[Dict] = None):
    """Helper to log download events"""
    log = DownloadLog(
        job_id=job_id,
        level=level,
        message=message,
        step=step,
        attachment_name=attachment_name,
        extra_metadata=extra_metadata
    )
    db.add(log)
    db.commit()


async def download_attachments_for_opportunity(
    db: Session, 
    opportunity_id: int, 
    job_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download all attachments for an opportunity from SAM.gov
    Job tracking ile
    
    Args:
        db: Database session
        opportunity_id: Opportunity database ID
        job_id: Optional job ID for tracking (if None, creates new job)
    
    Returns:
        Dict with job_id, downloaded_count, failed_count, total_attachments
    """
    # Create or get job
    if not job_id:
        job_id = str(uuid.uuid4())
        job = DownloadJob(
            job_id=job_id,
            opportunity_id=opportunity_id,
            status='pending'
        )
        db.add(job)
        db.commit()
    else:
        job = db.query(DownloadJob).filter(DownloadJob.job_id == job_id).first()
        if not job:
            raise ValueError(f"Job {job_id} not found")
    
    # Update job status
    job.status = 'running'
    job.started_at = datetime.now()
    db.commit()
    
    _log_download(db, job_id, 'INFO', f"Starting download for opportunity {opportunity_id}", step='init')
    logger.info(f"[Job {job_id}] Starting download for opportunity {opportunity_id}")
    
    try:
        # Get opportunity
        opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise ValueError(f"Opportunity {opportunity_id} not found")
        
        # Create directory structure
        notice_id = opportunity.notice_id or str(opportunity.id)
        opp_dir = Path(BASE_DATA_DIR) / "opportunities" / notice_id / "attachments"
        opp_dir.mkdir(parents=True, exist_ok=True)
        
        _log_download(db, job_id, 'INFO', f"Download directory: {opp_dir}", step='init', extra_metadata={"directory": str(opp_dir)})
        
        # Get all attachments that need downloading
        attachments = db.query(OpportunityAttachment).filter(
            OpportunityAttachment.opportunity_id == opportunity_id,
            OpportunityAttachment.source_url.isnot(None),
            OpportunityAttachment.downloaded == False
        ).all()
        
        job.total_attachments = len(attachments)
        db.commit()
        
        if not attachments:
            _log_download(db, job_id, 'INFO', "No attachments to download", step='complete')
            logger.info(f"[Job {job_id}] No attachments to download")
            job.status = 'completed'
            job.completed_at = datetime.now()
            db.commit()
            return {
                "job_id": job_id,
                "downloaded_count": 0,
                "failed_count": 0,
                "total_attachments": 0
            }
        
        _log_download(db, job_id, 'INFO', f"Found {len(attachments)} attachments to download", step='fetch', extra_metadata={"count": len(attachments)})
        
        downloaded_count = 0
        failed_count = 0
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            for idx, att in enumerate(attachments):
                try:
                    if not att.source_url:
                        _log_download(db, job_id, 'WARNING', f"Attachment {att.id} has no source_url, skipping", step='download', attachment_name=att.name)
                        continue
                    
                    # Generate safe filename
                    filename = att.name.replace("/", "_").replace("\\", "_")
                    filename = Path(filename).name
                    
                    # If no extension, try to guess from URL
                    if not Path(filename).suffix and att.mime_type:
                        ext_map = {
                            "application/pdf": ".pdf",
                            "application/msword": ".doc",
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
                            "application/vnd.ms-excel": ".xls",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
                        }
                        ext = ext_map.get(att.mime_type, "")
                        if ext:
                            filename = filename + ext
                    
                    local_path = opp_dir / filename
                    
                    # Skip if already exists
                    if local_path.exists():
                        _log_download(db, job_id, 'INFO', f"File already exists, skipping", step='download', attachment_name=att.name, extra_metadata={"path": str(local_path)})
                        att.local_path = str(local_path)
                        att.downloaded = True
                        att.size_bytes = local_path.stat().st_size
                        att.downloaded_at = datetime.now()
                        db.commit()
                        downloaded_count += 1
                        continue
                    
                    # Download file
                    _log_download(db, job_id, 'INFO', f"Downloading {att.name}", step='download', attachment_name=att.name, extra_metadata={"url": att.source_url})
                    logger.info(f"[Job {job_id}] Downloading {att.name} from {att.source_url}")
                    
                    response = await client.get(att.source_url)
                    response.raise_for_status()
                    
                    # Save to disk
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                    
                    # Update attachment record
                    att.local_path = str(local_path)
                    att.downloaded = True
                    att.size_bytes = len(response.content)
                    att.downloaded_at = datetime.now()
                    
                    # Update mime_type if not set
                    if not att.mime_type and response.headers.get("content-type"):
                        att.mime_type = response.headers.get("content-type").split(";")[0]
                    
                    db.commit()
                    db.refresh(att)
                    
                    _log_download(db, job_id, 'INFO', f"Downloaded {att.name} ({att.size_bytes} bytes)", step='save', attachment_name=att.name, extra_metadata={"size_bytes": att.size_bytes, "path": str(local_path)})
                    logger.info(f"[Job {job_id}] Downloaded {att.name} ({att.size_bytes} bytes) to {local_path}")
                    downloaded_count += 1
                    
                except httpx.HTTPStatusError as e:
                    error_msg = f"HTTP error {e.response.status_code}"
                    logger.error(f"[Job {job_id}] {error_msg} for {att.name}")
                    _log_download(db, job_id, 'ERROR', error_msg, step='download', attachment_name=att.name, extra_metadata={"status_code": e.response.status_code, "error": str(e)})
                    failed_count += 1
                    continue
                except Exception as e:
                    error_msg = f"Error downloading: {e}"
                    logger.error(f"[Job {job_id}] {error_msg} for {att.name}", exc_info=True)
                    _log_download(db, job_id, 'ERROR', error_msg, step='download', attachment_name=att.name, extra_metadata={"error": str(e)})
                    failed_count += 1
                    continue
        
        # Update job with results
        job.status = 'completed'
        job.completed_at = datetime.now()
        job.downloaded_count = downloaded_count
        job.failed_count = failed_count
        db.commit()
        
        _log_download(db, job_id, 'INFO', f"Download completed: {downloaded_count} downloaded, {failed_count} failed", step='complete', extra_metadata={"downloaded": downloaded_count, "failed": failed_count})
        logger.info(f"[Job {job_id}] Download completed: {downloaded_count} downloaded, {failed_count} failed")
        
        return {
            "job_id": job_id,
            "downloaded_count": downloaded_count,
            "failed_count": failed_count,
            "total_attachments": len(attachments)
        }
    
    except Exception as e:
        # Update job with error
        job.status = 'failed'
        job.completed_at = datetime.now()
        job.error_message = str(e)
        db.commit()
        
        _log_download(db, job_id, 'ERROR', f"Download failed: {e}", step='error', extra_metadata={"error": str(e)})
        logger.error(f"[Job {job_id}] Download failed: {e}", exc_info=True)
        raise


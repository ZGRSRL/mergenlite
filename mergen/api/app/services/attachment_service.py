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
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from sqlalchemy.orm import Session
from datetime import datetime

from ..models import Opportunity, OpportunityAttachment, DownloadJob, DownloadLog

logger = logging.getLogger(__name__)

# Base data directory
BASE_DATA_DIR = os.getenv("DATA_DIR", "data")
SAM_API_KEY = os.getenv("SAM_API_KEY")


def _build_download_url(raw_url: str) -> str:
    """Append SAM API key to download URLs if missing."""
    if not SAM_API_KEY:
        return raw_url
    try:
        parsed = urlparse(raw_url)
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        if "api_key" in query:
            return raw_url
        query["api_key"] = SAM_API_KEY
        new_query = urlencode(query)
        new_url = urlunparse(parsed._replace(query=new_query))
        return new_url
    except Exception:
        return raw_url


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
        
        # Get all attachments for this opportunity (for debugging)
        all_attachments = db.query(OpportunityAttachment).filter(
            OpportunityAttachment.opportunity_id == opportunity_id
        ).all()
        
        logger.info(f"[Job {job_id}] Total attachments in DB: {len(all_attachments)}")
        for att in all_attachments:
            logger.info(f"[Job {job_id}] Attachment {att.id}: name={att.name}, source_url={att.source_url}, downloaded={att.downloaded}, local_path={att.local_path}")
        
        # Get all attachments that need downloading
        attachments = db.query(OpportunityAttachment).filter(
            OpportunityAttachment.opportunity_id == opportunity_id,
            OpportunityAttachment.source_url.isnot(None),
            OpportunityAttachment.downloaded == False
        ).all()
        
        job.total_attachments = len(attachments)
        db.commit()
        
        if not attachments:
            # Check why no attachments
            attachments_without_url = db.query(OpportunityAttachment).filter(
                OpportunityAttachment.opportunity_id == opportunity_id,
                OpportunityAttachment.source_url.is_(None)
            ).count()
            already_downloaded = db.query(OpportunityAttachment).filter(
                OpportunityAttachment.opportunity_id == opportunity_id,
                OpportunityAttachment.downloaded == True
            ).count()
            
            logger.warning(f"[Job {job_id}] No attachments to download. Total: {len(all_attachments)}, Without URL: {attachments_without_url}, Already downloaded: {already_downloaded}")
            _log_download(db, job_id, 'WARNING', f"No attachments to download. Total: {len(all_attachments)}, Without URL: {attachments_without_url}, Already downloaded: {already_downloaded}", step='complete')
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
        
        # httpx client with redirect following enabled (for SAM.gov 303 redirects)
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
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
                    download_url = _build_download_url(att.source_url)
                    _log_download(
                        db,
                        job_id,
                        f"Downloading {att.name}",
                        step='download',
                        attachment_name=att.name,
                        extra_metadata={"url": download_url},
                    )
                    logger.info(f"[Job {job_id}] Downloading {att.name} from {download_url}")
                    
                    response = await client.get(download_url)
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
                    # Handle 303 redirects specially - try to follow Location header
                    if e.response.status_code == 303:
                        location = e.response.headers.get("Location")
                        if location:
                            logger.info(f"[Job {job_id}] Got 303 redirect for {att.name}, following to {location}")
                            try:
                                # Try downloading from the redirect location
                                redirect_response = await client.get(location)
                                redirect_response.raise_for_status()
                                
                                # Save to disk
                                with open(local_path, "wb") as f:
                                    f.write(redirect_response.content)
                                
                                # Update attachment record
                                att.local_path = str(local_path)
                                att.downloaded = True
                                att.size_bytes = len(redirect_response.content)
                                att.downloaded_at = datetime.now()
                                
                                # Update mime_type if not set
                                if not att.mime_type and redirect_response.headers.get("content-type"):
                                    att.mime_type = redirect_response.headers.get("content-type").split(";")[0]
                                
                                db.commit()
                                db.refresh(att)
                                
                                _log_download(db, job_id, 'INFO', f"Downloaded {att.name} via 303 redirect ({att.size_bytes} bytes)", step='save', attachment_name=att.name, extra_metadata={"size_bytes": att.size_bytes, "path": str(local_path), "redirect_url": location})
                                logger.info(f"[Job {job_id}] Downloaded {att.name} via 303 redirect ({att.size_bytes} bytes) to {local_path}")
                                downloaded_count += 1
                                continue
                            except Exception as redirect_err:
                                error_msg = f"HTTP 303 redirect failed: {redirect_err}"
                                logger.error(f"[Job {job_id}] {error_msg} for {att.name} (redirect to {location})")
                                _log_download(db, job_id, 'ERROR', error_msg, step='download', attachment_name=att.name, extra_metadata={"status_code": 303, "redirect_location": location, "error": str(redirect_err)})
                                failed_count += 1
                                continue
                        else:
                            error_msg = f"HTTP 303 redirect but no Location header"
                            logger.error(f"[Job {job_id}] {error_msg} for {att.name}")
                            _log_download(db, job_id, 'ERROR', error_msg, step='download', attachment_name=att.name, extra_metadata={"status_code": 303, "error": "No Location header"})
                            failed_count += 1
                            continue
                    else:
                        error_msg = f"HTTP error {e.response.status_code}"
                        logger.error(f"[Job {job_id}] {error_msg} for {att.name} (URL: {att.source_url})")
                        _log_download(db, job_id, 'ERROR', error_msg, step='download', attachment_name=att.name, extra_metadata={"status_code": e.response.status_code, "url": att.source_url, "error": str(e)})
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


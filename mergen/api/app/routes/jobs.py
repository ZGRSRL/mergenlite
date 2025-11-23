"""
Daily Job Routes
Endpoints for scheduled/automated jobs (Cloud Scheduler integration)
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from ..db import get_db, SessionLocal
from ..models import Opportunity, AIAnalysisResult
from ..services.pipeline_service import create_pipeline_job, run_pipeline_job
from ..services.sam_service import fetch_opportunities_from_sam
from ..services.sam_gov.integration import SAMGovIntegration
from ..crud.opportunities import create_or_update_opportunity

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


class DailyJobRequest(BaseModel):
    """Request model for daily scan job"""
    target_id: Optional[str] = "721110"  # NAICS code or opportunity ID
    naics_code: Optional[str] = "721110"  # NAICS code for SAM.gov search
    days_back: int = 1  # How many days back to search
    limit: int = 10  # Max opportunities to process
    force_refresh: bool = False  # Force re-analysis even if already analyzed


async def process_daily_scan_job(
    naics_code: str,
    days_back: int,
    limit: int,
    force_refresh: bool
):
    """
    Background task: Fetch opportunities, analyze, and send emails.
    This runs asynchronously so Cloud Scheduler doesn't timeout.
    """
    db = SessionLocal()
    try:
        logger.info(f"📅 GÜNLÜK GÖREV BAŞLADI: NAICS {naics_code}, Son {days_back} gün, Max {limit} ilan")
        
        # Step 1: Fetch opportunities from SAM.gov
        logger.info(f"🔍 SAM.gov'dan veri çekiliyor (NAICS: {naics_code})...")
        try:
            # Try SAM.gov integration first
            sam_integration = SAMGovIntegration()
            opportunities = await sam_integration.search_opportunities(
                naics_codes=[naics_code],
                date_range_days=days_back
            )
            
            if not opportunities:
                # Fallback to legacy SAM service
                logger.info("SAM.gov integration returned no results, trying legacy SAM service...")
                opportunities = await fetch_opportunities_from_sam({
                    "naics": naics_code,
                    "days_back": days_back,
                    "limit": limit
                })
                # Convert to list if needed
                if not isinstance(opportunities, list):
                    opportunities = []
        except Exception as sam_error:
            logger.error(f"❌ SAM.gov veri çekme hatası: {sam_error}", exc_info=True)
            opportunities = []
        
        if not opportunities:
            logger.warning(f"⚠️  NAICS {naics_code} için ilan bulunamadı")
            return {
                "status": "completed",
                "message": f"No opportunities found for NAICS {naics_code}",
                "opportunities_processed": 0
            }
        
        # Limit to max opportunities
        opportunities = opportunities[:limit]
        logger.info(f"✅ {len(opportunities)} ilan bulundu, analiz başlatılıyor...")
        
        # Step 2: Process each opportunity
        processed_count = 0
        analyzed_count = 0
        errors = []
        
        for opp_data in opportunities:
            try:
                notice_id = opp_data.get('noticeId') or opp_data.get('notice_id') or opp_data.get('id')
                if not notice_id:
                    logger.warning(f"Skipping opportunity without notice_id: {opp_data.get('title', 'Unknown')[:50]}")
                    continue
                
                # Check if already analyzed (unless force_refresh)
                if not force_refresh:
                    existing = db.query(Opportunity).filter(
                        Opportunity.notice_id == str(notice_id)
                    ).first()
                    
                    if existing:
                        # Check if already analyzed
                        existing_analysis = db.query(AIAnalysisResult).filter(
                            AIAnalysisResult.opportunity_id == existing.id,
                            AIAnalysisResult.analysis_type.in_(["sow_draft", "sow"]),
                            AIAnalysisResult.status == "completed"
                        ).first()
                        
                        if existing_analysis:
                            logger.info(f"⏭️  İlan {notice_id} zaten analiz edilmiş, atlanıyor")
                            continue
                
                # Create or update opportunity in database
                try:
                    # Map SAM data to Opportunity model
                    opp_dict = map_sam_record_to_opportunity(opp_data)
                    
                    # Use upsert_opportunity from CRUD
                    from ..crud.opportunities import upsert_opportunity
                    opportunity = upsert_opportunity(db, opp_dict)
                except Exception as db_error:
                    logger.error(f"⚠️  İlan {notice_id} veritabanına kaydedilemedi: {db_error}")
                    continue
                
                logger.info(f"📄 İlan {notice_id} analiz ediliyor (Opportunity ID: {opportunity.id})...")
                
                # Step 3: Run SOW analysis
                analysis_result, agent_run_id = create_pipeline_job(
                    db=db,
                    opportunity_id=opportunity.id,
                    analysis_type="sow_draft",
                    pipeline_version="v1",
                    agent_name="autogen",
                    initial_options={}
                )
                
                # Run analysis synchronously (we're already in background task)
                payload = {
                    "opportunity_id": opportunity.id,
                    "analysis_type": "sow_draft",
                    "pipeline_version": "v1",
                    "agent_name": "autogen",
                    "options": {},
                    "agent_run_id": agent_run_id
                }
                
                run_pipeline_job(analysis_result.id, payload)
                
                analyzed_count += 1
                processed_count += 1
                
                logger.info(f"✅ İlan {notice_id} analizi tamamlandı (Analysis ID: {analysis_result.id})")
                
                # Small delay to avoid overwhelming the system
                import time
                time.sleep(2)
                
            except Exception as opp_error:
                error_msg = f"İlan {notice_id} işlenirken hata: {opp_error}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
                continue
        
        result = {
            "status": "completed",
            "message": f"Günlük görev tamamlandı: {processed_count} ilan işlendi, {analyzed_count} analiz yapıldı",
            "opportunities_found": len(opportunities),
            "opportunities_processed": processed_count,
            "analyses_completed": analyzed_count,
            "errors": errors if errors else None
        }
        
        logger.info(f"✅✅✅ GÜNLÜK GÖREV TAMAMLANDI: {result['message']}")
        return result
        
    except Exception as e:
        logger.error(f"❌ GÜNLÜK GÖREV HATASI: {e}", exc_info=True)
        return {
            "status": "failed",
            "message": f"Günlük görev hatası: {e}",
            "error": str(e)
        }
    finally:
        db.close()


@router.post("/daily-scan")
async def trigger_daily_scan(
    job: DailyJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Cloud Scheduler tarafından her sabah tetiklenecek endpoint.
    
    NAICS kodu 721110 (Hotel/Motel) için SAM.gov'dan yeni ilanları çeker,
    analiz eder ve e-posta gönderir.
    
    Background task olarak çalışır, hemen 202 Accepted döner.
    """
    logger.info(f"📅 GÜNLÜK GÖREV TETİKLENDİ: NAICS {job.naics_code or job.target_id}")
    
    # İşlemi arka plana at (Cloud Scheduler timeout yemesin diye hemen 202 dönüyoruz)
    background_tasks.add_task(
        process_daily_scan_job,
        naics_code=job.naics_code or job.target_id or "721110",
        days_back=job.days_back,
        limit=job.limit,
        force_refresh=job.force_refresh
    )
    
    return {
        "status": "accepted",
        "message": f"Günlük analiz başlatıldı. Hedef: NAICS {job.naics_code or job.target_id}",
        "target_id": job.target_id,
        "naics_code": job.naics_code or job.target_id,
        "days_back": job.days_back,
        "limit": job.limit,
        "force_refresh": job.force_refresh
    }


@router.get("/daily-scan/status")
async def get_daily_scan_status(
    naics_code: str = "721110",
    days_back: int = 1,
    db: Session = Depends(get_db)
):
    """
    Son günlük tarama durumunu kontrol et.
    """
    # Get recent opportunities for this NAICS code
    from datetime import datetime, timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    opportunities = db.query(Opportunity).filter(
        Opportunity.naics_code == naics_code,
        Opportunity.posted_date >= cutoff_date
    ).order_by(Opportunity.posted_date.desc()).limit(20).all()
    
    # Check analysis status for each
    status_summary = []
    for opp in opportunities:
        analyses = db.query(AIAnalysisResult).filter(
            AIAnalysisResult.opportunity_id == opp.id
        ).order_by(AIAnalysisResult.created_at.desc()).all()
        
        status_summary.append({
            "opportunity_id": opp.id,
            "notice_id": opp.notice_id,
            "title": opp.title[:100] if opp.title else "N/A",
            "posted_date": opp.posted_date.isoformat() if opp.posted_date else None,
            "analyses_count": len(analyses),
            "latest_analysis": {
                "id": analyses[0].id,
                "type": analyses[0].analysis_type,
                "status": analyses[0].status,
                "created_at": analyses[0].created_at.isoformat() if analyses[0].created_at else None
            } if analyses else None
        })
    
    return {
        "naics_code": naics_code,
        "days_back": days_back,
        "opportunities_found": len(opportunities),
        "opportunities": status_summary
    }


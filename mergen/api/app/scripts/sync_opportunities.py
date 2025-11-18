"""
Scheduled job to sync opportunities from SAM.gov
Run hourly via cron or RQ scheduler
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db import SessionLocal
from app.models import Opportunity
from sam_integration import SAMIntegration
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def sync_naics_721110(days_back: int = 30, limit: int = 1000):
    """
    Sync NAICS 721110 (Hotel/Motel) opportunities
    """
    db = SessionLocal()
    
    try:
        logger.info(f"🔄 Starting sync for NAICS 721110 (days_back={days_back}, limit={limit})")
        
        sam = SAMIntegration()
        
        # Fetch opportunities
        opportunities = sam.fetch_opportunities(
            naics_codes=['721110'],
            days_back=days_back,
            limit=limit,
            page_size=1000
        )
        
        logger.info(f"📥 Fetched {len(opportunities)} opportunities from SAM.gov")
        
        count_new = 0
        count_updated = 0
        
        for opp_data in opportunities:
            notice_id = opp_data.get('noticeId') or opp_data.get('opportunityId', '')
            if not notice_id:
                continue
            
            existing = db.query(Opportunity).filter(Opportunity.notice_id == notice_id).first()
            
            if existing:
                # Update
                existing.title = opp_data.get('title', existing.title)
                existing.opportunity_id = opp_data.get('opportunityId', existing.opportunity_id)
                existing.naics_code = opp_data.get('naicsCode', existing.naics_code)
                existing.organization = opp_data.get('fullParentPathName', existing.organization)
                existing.raw_json = opp_data
                existing.source = opp_data.get('source', 'sam_live')
                existing.updated_at = datetime.now()
                count_updated += 1
            else:
                # Create
                new_opp = Opportunity(
                    notice_id=notice_id,
                    opportunity_id=opp_data.get('opportunityId', ''),
                    title=opp_data.get('title', ''),
                    naics_code=opp_data.get('naicsCode', ''),
                    organization=opp_data.get('fullParentPathName', ''),
                    posted_date=_parse_date(opp_data.get('postedDate')),
                    response_deadline=_parse_date(opp_data.get('responseDeadLine')),
                    source=opp_data.get('source', 'sam_live'),
                    raw_json=opp_data
                )
                db.add(new_opp)
                count_new += 1
        
        db.commit()
        
        logger.info(f"✅ Sync complete: {count_new} new, {count_updated} updated")
        
        return {
            "success": True,
            "count_new": count_new,
            "count_updated": count_updated,
            "total_processed": len(opportunities)
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Sync failed: {e}")
        raise
    finally:
        db.close()


def _parse_date(date_str):
    """Parse date string to datetime"""
    if not date_str or date_str == 'N/A':
        return None
    try:
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%Y-%m-%dT%H:%M:%S']:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue
        return None
    except:
        return None


if __name__ == "__main__":
    # Default: sync last 30 days, max 1000 opportunities
    sync_naics_721110(days_back=30, limit=1000)


"""
Dashboard API Routes
- Statistics and KPIs
- Recent activities
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from ..db import get_db
from ..models import Opportunity

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics and KPIs
    """
    try:
        # Total opportunities count - use opportunity_id (primary key) instead of id
        try:
            total_opportunities = db.query(func.count(Opportunity.opportunity_id)).scalar() or 0
        except Exception:
            # Fallback: try id if opportunity_id doesn't work
            try:
                total_opportunities = db.query(func.count(Opportunity.id)).scalar() or 0
            except Exception:
                total_opportunities = 0
        
        # Today's new opportunities - use created_at if available
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        try:
            today_new = db.query(func.count(Opportunity.opportunity_id)).filter(
                Opportunity.created_at >= today_start
            ).scalar() or 0
        except Exception:
            # Fallback: try id if opportunity_id doesn't work
            try:
                today_new = db.query(func.count(Opportunity.id)).filter(
                    Opportunity.created_at >= today_start
                ).scalar() or 0
            except Exception:
                today_new = 0
        
        # Analyzed opportunities count - check cached_data for analysis
        try:
            # Check if cached_data contains analysis
            analyzed_count = db.query(func.count(Opportunity.opportunity_id)).filter(
                Opportunity.cached_data.isnot(None)
            ).scalar() or 0
        except Exception:
            try:
                analyzed_count = db.query(func.count(Opportunity.id)).filter(
                    Opportunity.cached_data.isnot(None)
                ).scalar() or 0
            except Exception:
                analyzed_count = 0
        
        # Average analysis time (mock for now, can be calculated from analysis logs)
        avg_analysis_time = "28sn"  # TODO: Calculate from actual analysis logs
        
        return {
            "total_opportunities": total_opportunities,
            "today_new": today_new,
            "analyzed_count": analyzed_count,
            "avg_analysis_time": avg_analysis_time,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@router.get("/recent-activities")
async def get_recent_activities(
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get recent activities (recent opportunities)
    """
    try:
        # Get recent opportunities - try posted_date first, fallback to created_at
        try:
            opportunities = db.query(Opportunity).order_by(
                Opportunity.posted_date.desc().nulls_last()
            ).limit(limit).all()
        except Exception:
            # Fallback: use created_at if posted_date doesn't exist
            try:
                opportunities = db.query(Opportunity).order_by(
                    Opportunity.created_at.desc()
                ).limit(limit).all()
            except Exception:
                # Last fallback: no ordering
                opportunities = db.query(Opportunity).limit(limit).all()
        
        result = []
        for opp in opportunities:
            # Calculate days left
            days_left = 0
            if opp.response_deadline:
                delta = opp.response_deadline - datetime.now()
                days_left = max(0, delta.days)
            
            # Determine risk based on days left
            if days_left <= 5:
                risk = 'high'
            elif days_left <= 10:
                risk = 'medium'
            else:
                risk = 'low'
            
            # Extract data from raw_data (or raw_json alias) if available
            raw_data = opp.raw_data if hasattr(opp, 'raw_data') and opp.raw_data else {}
            if not raw_data and hasattr(opp, 'raw_json'):
                raw_data = opp.raw_json or {}
            if not raw_data and hasattr(opp, 'cached_data'):
                raw_data = opp.cached_data or {}
            
            # Get ID - try id first, fallback to opportunity_id
            opp_id = getattr(opp, 'id', None) or getattr(opp, 'opportunity_id', 'unknown')
            
            result.append({
                "id": f"AN-{opp_id}",
                "noticeId": opp.notice_id or "",
                "title": opp.title or "Başlık Yok",
                "risk": risk,
                "daysLeft": days_left,
                "publishedDate": opp.posted_date.isoformat() if hasattr(opp, 'posted_date') and opp.posted_date else None,
                "responseDeadline": opp.response_deadline.isoformat() if opp.response_deadline else None,
                "samGovLink": raw_data.get("uiLink") or raw_data.get("samGovLink") or f"https://sam.gov/opp/{opp.opportunity_id}/view" if opp.opportunity_id else None,
            })
        
        return {
            "activities": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching activities: {str(e)}")


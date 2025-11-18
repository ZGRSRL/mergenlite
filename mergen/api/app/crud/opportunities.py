"""
CRUD operations for Opportunities
"""
import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import Opportunity, OpportunityAttachment
from ..schemas import OpportunityCreate, OpportunityAttachmentCreate

logger = logging.getLogger(__name__)


def upsert_opportunity(db: Session, data: Dict[str, Any]) -> Opportunity:
    """
    notice_id üzerinden upsert.
    Eğer varsa güncelle, yoksa oluştur.
    
    Args:
        db: Database session
        data: OpportunityCreate formatında dict
    
    Returns:
        Opportunity model instance
    """
    notice_id = data.get("notice_id")
    if not notice_id:
        raise ValueError("notice_id is required")
    
    # Try to find by notice_id first
    obj = db.query(Opportunity).filter(Opportunity.notice_id == notice_id).first()
    
    # Fallback: try by opportunity_id if notice_id not found
    if not obj and data.get("opportunity_id"):
        obj = db.query(Opportunity).filter(Opportunity.opportunity_id == data.get("opportunity_id")).first()
    
    if obj:
        # Update existing
        for key, value in data.items():
            if hasattr(obj, key) and value is not None:
                setattr(obj, key, value)
        obj.updated_at = datetime.now()
        logger.debug(f"Updated opportunity: {notice_id}")
    else:
        # Create new
        obj = Opportunity(**data)
        db.add(obj)
        logger.debug(f"Created new opportunity: {notice_id}")
    
    try:
        db.commit()
        db.refresh(obj)
    except Exception as e:
        db.rollback()
        logger.error(f"Error upserting opportunity {notice_id}: {e}", exc_info=True)
        raise
    
    return obj


def get_opportunity(db: Session, opportunity_id: int) -> Optional[Opportunity]:
    """Get opportunity by database ID"""
    return db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()


def get_opportunity_by_notice_id(db: Session, notice_id: str) -> Optional[Opportunity]:
    """Get opportunity by notice_id"""
    return db.query(Opportunity).filter(Opportunity.notice_id == notice_id).first()


def list_opportunities(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    naics_code: Optional[str] = None,
    keyword: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> List[Opportunity]:
    """List opportunities with filters"""
    query = db.query(Opportunity)
    
    if naics_code:
        query = query.filter(Opportunity.naics_code == naics_code)
    
    if keyword:
        like_pattern = f"%{keyword}%"
        query = query.filter(
            (Opportunity.title.ilike(like_pattern)) |
            (Opportunity.description.ilike(like_pattern))
        )
    
    if date_from:
        query = query.filter(Opportunity.posted_date >= date_from)
    
    if date_to:
        query = query.filter(Opportunity.posted_date <= date_to)
    
    # Order by posted_date desc, nulls last
    try:
        from sqlalchemy import desc
        query = query.order_by(desc(Opportunity.posted_date).nulls_last())
    except Exception:
        # Fallback: simple order
        query = query.order_by(Opportunity.posted_date.desc())
    
    return query.offset(skip).limit(limit).all()


def create_attachment(db: Session, attachment_data: Dict[str, Any]) -> OpportunityAttachment:
    """Create an attachment record"""
    attachment = OpportunityAttachment(**attachment_data)
    db.add(attachment)
    try:
        db.commit()
        db.refresh(attachment)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating attachment: {e}", exc_info=True)
        raise
    return attachment


def get_attachments_for_opportunity(db: Session, opportunity_id: int) -> List[OpportunityAttachment]:
    """Get all attachments for an opportunity"""
    return db.query(OpportunityAttachment).filter(
        OpportunityAttachment.opportunity_id == opportunity_id
    ).all()


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..db import get_db
from ..models import Document

router = APIRouter()


@router.get("/matrix")
async def get_compliance_matrix(
    rfq_id: int,
    db: Session = Depends(get_db)
):
    """Get compliance matrix for an RFQ"""
    
    # Check if RFQ exists
    rfq_doc = db.query(Document).filter(
        Document.id == rfq_id,
        Document.kind == "rfq"
    ).first()
    
    if not rfq_doc:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    # Return empty matrix for now - can be extended later with Document-based compliance
    return {
        "rfq_id": rfq_id,
        "items": [],
        "total_requirements": 0,
        "compliant": 0,
        "non_compliant": 0,
        "partial": 0
    }


@router.get("/requirements/{rfq_id}")
async def get_requirements(
    rfq_id: int,
    db: Session = Depends(get_db)
):
    """Get all requirements for an RFQ"""
    
    # Check if RFQ exists
    rfq_doc = db.query(Document).filter(
        Document.id == rfq_id,
        Document.kind == "rfq"
    ).first()
    
    if not rfq_doc:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    # Return empty list for now - requirements can be extracted from Document.meta_json later
    return []


@router.get("/evidence/{requirement_id}")
async def get_evidence(
    requirement_id: int,
    db: Session = Depends(get_db)
):
    """Get evidence for a specific requirement"""
    
    # Return empty list for now - evidence can be stored in Document.meta_json later
    return []


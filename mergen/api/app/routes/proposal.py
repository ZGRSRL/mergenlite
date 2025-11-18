from fastapi import APIRouter, Depends, HTTPException, Response, Query
from sqlalchemy.orm import Session
from typing import Optional
import sys
import os

from ..db import get_db
from ..models import Document, Opportunity
from ..schemas import ProposalDraft
from ..services.proposal.composer import generate_proposal_draft

# Add root to path for imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
if ROOT not in sys.path:
    sys.path.append(ROOT)

# Import SAMIntegration with fallback
# SAMIntegration import - optional
try:
    from sam_integration import SAMIntegration  # type: ignore
except ImportError:
    try:
        import sys
        import os
        from pathlib import Path
        # Add project root to path
        project_root = Path(__file__).parent.parent.parent.parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        from sam_integration import SAMIntegration  # type: ignore
    except ImportError:
        SAMIntegration = None  # type: ignore
        print("[proposal.py] Warning: SAMIntegration not available. Some features may be disabled.")

router = APIRouter()


@router.post("/draft", response_model=ProposalDraft)
async def generate_draft_proposal(
    rfq_id: int,
    format: str = "json",  # json, docx, pdf
    db: Session = Depends(get_db)
):
    """Generate draft proposal for an RFQ"""
    
    # Check if RFQ exists
    rfq_doc = db.query(Document).filter(
        Document.id == rfq_id,
        Document.kind == "rfq"
    ).first()
    
    if not rfq_doc:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    # Generate proposal draft
    proposal = generate_proposal_draft(db, rfq_id)
    
    return proposal


@router.post("/auto")
async def auto_analyze(
    notice_id: str = Query(..., description="Notice ID to analyze"),
    db: Session = Depends(get_db)
):
    """
    Auto analyze opportunity: Download documents, parse RFQ, generate proposal
    Returns: rfq_id, docs_count, compliance.overall_risk, proposal.summary
    """
    try:
        # 1. Get opportunity details and download documents
        sam = SAMIntegration()
        downloaded = sam.download_documents(notice_id, dest_dir="downloads")
        
        if not downloaded:
            raise HTTPException(status_code=404, detail=f"No documents found for Notice ID: {notice_id}")
        
        # 2. Create Document records for downloaded files
        doc_ids = []
        for doc_info in downloaded:
            doc = Document(
                kind="rfq",
                title=doc_info['title'],
                path=doc_info['path'],
                meta_json={
                    "notice_id": notice_id,
                    "filename": doc_info['filename'],
                    "url": doc_info['url'],
                    "type": doc_info['type']
                }
            )
            db.add(doc)
            db.flush()
            doc_ids.append(doc.id)
        
        db.commit()
        
        # 3. Use first document as RFQ for analysis
        rfq_id = doc_ids[0] if doc_ids else None
        
        if not rfq_id:
            raise HTTPException(status_code=500, detail="Failed to create document records")
        
        # 4. Generate proposal draft
        try:
            proposal = generate_proposal_draft(db, rfq_id)
        except Exception as e:
            # Proposal generation is optional, continue without it
            proposal = None
        
        return {
            "success": True,
            "notice_id": notice_id,
            "rfq_id": rfq_id,
            "docs_count": len(downloaded),
            "compliance": {
                "overall_risk": "medium"  # Placeholder, should be calculated
            },
            "proposal": {
                "summary": proposal.summary if proposal else "Analysis in progress"
            } if proposal else {"summary": "Analysis in progress"}
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto analyze error: {str(e)}")


@router.get("/draft/{rfq_id}/download")
async def download_proposal(
    rfq_id: int,
    format: str = "docx",
    db: Session = Depends(get_db)
):
    """Download proposal in specified format"""
    
    # Check if RFQ exists
    rfq_doc = db.query(Document).filter(
        Document.id == rfq_id,
        Document.kind == "rfq"
    ).first()
    
    if not rfq_doc:
        raise HTTPException(status_code=404, detail="RFQ not found")
    
    # Generate and return file
    if format == "docx":
        file_content = generate_proposal_draft(db, rfq_id, format="docx")
        return Response(
            content=file_content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename=proposal_{rfq_id}.docx"}
        )
    elif format == "pdf":
        file_content = generate_proposal_draft(db, rfq_id, format="pdf")
        return Response(
            content=file_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=proposal_{rfq_id}.pdf"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")




from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from ...models import Document
from ...schemas import ProposalDraft
from ..llm.router import generate_text
from ..llm.prompts import (
    get_executive_summary_prompt,
    get_technical_approach_prompt,
    get_past_performance_prompt,
    get_pricing_summary_prompt
)
from ..pricing.engine import calculate_quote
import logging

logger = logging.getLogger(__name__)


def generate_proposal_draft(
    db: Session,
    rfq_id: int,
    format: str = "json"
) -> ProposalDraft:
    """Generate draft proposal for an RFQ"""
    logger.info(f"Generating proposal draft for RFQ {rfq_id}")
    
    # Get RFQ document
    rfq_doc = db.query(Document).filter(
        Document.id == rfq_id,
        Document.kind == "rfq"
    ).first()
    
    if not rfq_doc:
        raise ValueError(f"RFQ document {rfq_id} not found")
    
    # Build empty compliance matrix for now
    compliance_matrix = {
        "rfq_id": rfq_id,
        "items": [],
        "total_requirements": 0,
        "met_requirements": 0,
        "gap_requirements": 0,
        "overall_risk": "low"
    }
    
    # Get pricing items - empty for now
    pricing_items = []
    
    # Get past performance - empty for now
    past_performance = []
    
    # Generate sections
    executive_summary = generate_executive_summary(
        rfq_doc.title, compliance_matrix, pricing_items
    )
    
    technical_approach = generate_technical_approach(
        db, rfq_id, compliance_matrix
    )
    
    past_performance_section = generate_past_performance_section(
        past_performance, compliance_matrix
    )
    
    pricing_summary = generate_pricing_summary_section(pricing_items)
    
    # Create proposal draft
    proposal = ProposalDraft(
        rfq_id=rfq_id,
        executive_summary=executive_summary,
        technical_approach=technical_approach,
        past_performance=past_performance_section,
        pricing_summary=pricing_summary,
        compliance_matrix=compliance_matrix,
        created_at=datetime.now()
    )
    
    return proposal


def generate_executive_summary(
    rfq_title: str,
    compliance_matrix: dict,
    pricing_items: list
) -> str:
    """Generate executive summary section"""
    logger.info("Generating executive summary")
    
    # Extract key information
    key_risks = []
    mitigation_strategies = []
    
    # Build prompt
    prompt = get_executive_summary_prompt(
        rfq_title,
        {
            "total_requirements": compliance_matrix.get("total_requirements", 0),
            "met_requirements": compliance_matrix.get("met_requirements", 0),
            "gap_requirements": compliance_matrix.get("gap_requirements", 0),
            "overall_risk": compliance_matrix.get("overall_risk", "low")
        },
        key_risks,
        mitigation_strategies
    )
    
    # Generate text using LLM
    try:
        summary = generate_text(prompt)
        return summary
    except Exception as e:
        logger.error(f"Error generating executive summary: {e}")
        return f"Executive summary generation failed: {str(e)}"


def generate_technical_approach(
    db: Session,
    rfq_id: int,
    compliance_matrix: dict
) -> str:
    """Generate technical approach section"""
    logger.info("Generating technical approach")
    
    # Get RFQ document
    rfq_doc = db.query(Document).filter(
        Document.id == rfq_id,
        Document.kind == "rfq"
    ).first()
    
    if not rfq_doc:
        return "No RFQ document found for technical approach."
    
    # Get facility features
    facility_features = db.query(Document).filter(
        Document.kind == "facility"
    ).first()
    
    facility_data = []
    if facility_features:
        # Extract facility features from document meta_json if available
        if facility_features.meta_json:
            facility_data = facility_features.meta_json.get("features", [])
        else:
            facility_data = [{"name": "placeholder", "value": "facility features"}]
    
    # Get past performance - empty for now
    past_perf_data = []
    
    # Generate basic technical approach
    approach_sections = []
    
    # Build prompt with RFQ document info
    prompt = get_technical_approach_prompt(
        {"title": rfq_doc.title, "path": rfq_doc.path},
        [],
        facility_data,
        past_perf_data
    )
    
    # Generate text
    try:
        section = generate_text(prompt)
        approach_sections.append(section)
    except Exception as e:
        logger.error(f"Error generating technical approach: {e}")
        approach_sections.append(f"Error generating content: {str(e)}")
    
    return "\n\n".join(approach_sections) if approach_sections else "No technical approach generated."


def generate_past_performance_section(
    past_performance: list,
    compliance_matrix: dict
) -> str:
    """Generate past performance section"""
    logger.info("Generating past performance section")
    
    if not past_performance:
        return "No past performance information available."
    
    # Convert to dict format (past_performance is already a list of dicts or empty)
    past_perf_data = past_performance if isinstance(past_performance, list) else []
    
    # Build prompt
    prompt = get_past_performance_prompt(
        past_perf_data,
        "Government conference and event management services"
    )
    
    # Generate text
    try:
        section = generate_text(prompt)
        return section
    except Exception as e:
        logger.error(f"Error generating past performance section: {e}")
        return f"Past performance section generation failed: {str(e)}"


def generate_pricing_summary_section(pricing_items: list) -> str:
    """Generate pricing summary section"""
    logger.info("Generating pricing summary section")
    
    if not pricing_items:
        return "No pricing information available."
    
    # Calculate quote
    quote = calculate_quote(pricing_items)
    
    # Check per-diem compliance
    per_diem_compliance = True  # TODO: Implement actual check
    
    # Build prompt
    prompt = get_pricing_summary_prompt(
        quote["items"],
        quote["grand_total"],
        per_diem_compliance
    )
    
    # Generate text
    try:
        section = generate_text(prompt)
        return section
    except Exception as e:
        logger.error(f"Error generating pricing summary section: {e}")
        return f"Pricing summary section generation failed: {str(e)}"


def generate_compliance_matrix_section(compliance_matrix: dict) -> str:
    """Generate compliance matrix section"""
    logger.info("Generating compliance matrix section")
    
    matrix_lines = []
    matrix_lines.append("# Compliance Matrix")
    matrix_lines.append("")
    matrix_lines.append("| Requirement | Status | Evidence | Risk | Gap Analysis |")
    matrix_lines.append("|-------------|--------|----------|------|--------------|")
    
    items = compliance_matrix.get("items", [])
    for item in items:
        risk_level = item.get("risk_level", "low") if isinstance(item, dict) else getattr(item, "risk_level", "low")
        status = "Met" if risk_level in ["low", "medium"] else "Gap"
        evidence_text = "N/A"
        
        matrix_lines.append(
            f"| {item.get('requirement', {}).get('code', 'N/A') if isinstance(item, dict) else getattr(item, 'requirement', {}).get('code', 'N/A')} | {status} | {evidence_text} | "
            f"{risk_level} | N/A |"
        )
    
    return "\n".join(matrix_lines)

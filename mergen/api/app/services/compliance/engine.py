from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ...models import Requirement, Evidence, FacilityFeature, PricingItem, Clause
from ...schemas import ComplianceMatrix, ComplianceMatrixItem
from .rules import (
    check_per_diem_compliance,
    check_facility_compliance,
    check_distance_compliance,
    check_far_clause_compliance,
    check_ipp_billing_compliance
)
import logging

logger = logging.getLogger(__name__)


def calculate_risk_level(requirement: Requirement, evidence: List[Evidence]) -> str:
    """Calculate risk level for a requirement based on evidence"""
    if not evidence:
        return "critical"
    
    # Calculate average evidence score
    avg_score = sum(e.score for e in evidence) / len(evidence)
    
    if avg_score >= 0.8:
        return "low"
    elif avg_score >= 0.6:
        return "medium"
    elif avg_score >= 0.4:
        return "high"
    else:
        return "critical"


def find_best_evidence(requirement: Requirement, all_evidence: List[Evidence]) -> List[Evidence]:
    """Find best evidence for a requirement"""
    # Filter evidence for this requirement
    requirement_evidence = [e for e in all_evidence if e.requirement_id == requirement.id]
    
    # Sort by score (highest first)
    requirement_evidence.sort(key=lambda x: x.score, reverse=True)
    
    # Return top 3 evidence items
    return requirement_evidence[:3]


def generate_gap_analysis(requirement: Requirement, evidence: List[Evidence]) -> str:
    """Generate gap analysis for a requirement"""
    if not evidence:
        return f"No evidence found for requirement: {requirement.text[:100]}..."
    
    if len(evidence) == 1 and evidence[0].score < 0.5:
        return f"Limited evidence found. Score: {evidence[0].score:.2f}"
    
    return "Evidence found and requirements appear to be met."


def generate_mitigation_strategy(requirement: Requirement, evidence: List[Evidence], risk_level: str) -> str:
    """Generate mitigation strategy for a requirement"""
    if risk_level == "low":
        return "No mitigation needed. Requirements are well supported."
    
    elif risk_level == "medium":
        return "Consider gathering additional evidence or clarifying requirements."
    
    elif risk_level == "high":
        return "Immediate action required. Gather additional evidence and document assumptions."
    
    else:  # critical
        return "Critical gap identified. Must address before proposal submission."


def build_compliance_matrix(db: Session, rfq_id: int) -> ComplianceMatrix:
    """Build compliance matrix for an RFQ"""
    logger.info(f"Building compliance matrix for RFQ {rfq_id}")
    
    # Get all requirements for this RFQ
    requirements = db.query(Requirement).filter(Requirement.rfq_id == rfq_id).all()
    
    if not requirements:
        logger.warning(f"No requirements found for RFQ {rfq_id}")
        return ComplianceMatrix(
            rfq_id=rfq_id,
            items=[],
            overall_risk="unknown",
            total_requirements=0,
            met_requirements=0,
            gap_requirements=0
        )
    
    # Get all evidence
    all_evidence = db.query(Evidence).join(Requirement).filter(
        Requirement.rfq_id == rfq_id
    ).all()
    
    # Build compliance matrix items
    matrix_items = []
    met_count = 0
    gap_count = 0
    
    for requirement in requirements:
        # Find best evidence for this requirement
        evidence = find_best_evidence(requirement, all_evidence)
        
        # Calculate risk level
        risk_level = calculate_risk_level(requirement, evidence)
        
        # Generate gap analysis
        gap_analysis = generate_gap_analysis(requirement, evidence)
        
        # Generate mitigation strategy
        mitigation = generate_mitigation_strategy(requirement, evidence, risk_level)
        
        # Count met vs gap requirements
        if risk_level in ["low", "medium"]:
            met_count += 1
        else:
            gap_count += 1
        
        matrix_item = ComplianceMatrixItem(
            requirement=requirement,
            evidence=evidence,
            risk_level=risk_level,
            gap_analysis=gap_analysis,
            mitigation=mitigation
        )
        
        matrix_items.append(matrix_item)
    
    # Calculate overall risk
    if gap_count == 0:
        overall_risk = "low"
    elif gap_count <= len(requirements) * 0.3:
        overall_risk = "medium"
    elif gap_count <= len(requirements) * 0.6:
        overall_risk = "high"
    else:
        overall_risk = "critical"
    
    return ComplianceMatrix(
        rfq_id=rfq_id,
        items=matrix_items,
        overall_risk=overall_risk,
        total_requirements=len(requirements),
        met_requirements=met_count,
        gap_requirements=gap_count
    )


def check_regulatory_compliance(db: Session, rfq_id: int) -> Dict[str, Any]:
    """Check regulatory compliance (FAR clauses, IPP billing, etc.)"""
    logger.info(f"Checking regulatory compliance for RFQ {rfq_id}")
    
    # Get facility features
    facility_features = db.query(FacilityFeature).join(Clause).filter(
        Clause.document_id == rfq_id
    ).all()
    
    # Get pricing items for per-diem check
    pricing_items = db.query(PricingItem).filter(PricingItem.rfq_id == rfq_id).all()
    
    # Get FAR clauses
    clauses = db.query(Clause).filter(Clause.document_id == rfq_id).all()
    
    # Check facility compliance
    facility_compliance = check_facility_compliance([
        {"name": f.name, "value": f.value} for f in facility_features
    ])
    
    # Check per-diem compliance
    per_diem_warnings = []
    for item in pricing_items:
        if item.category == "lodging" and item.unit_price > 0:
            compliance = check_per_diem_compliance(
                item.unit_price, "orlando", "april"  # TODO: Extract from RFQ
            )
            if not compliance["compliant"]:
                per_diem_warnings.append(compliance["warning"])
    
    # Check FAR clause compliance
    far_compliance = check_far_clause_compliance([
        {"text": c.text, "tags": c.tags} for c in clauses
    ])
    
    # Check IPP billing compliance (placeholder)
    ipp_compliance = check_ipp_billing_compliance({
        "uses_ipp": True,  # TODO: Extract from RFQ
        "fields": [],  # TODO: Extract from RFQ
        "documents": []  # TODO: Extract from RFQ
    })
    
    return {
        "facility_compliance": facility_compliance,
        "per_diem_warnings": per_diem_warnings,
        "far_compliance": far_compliance,
        "ipp_compliance": ipp_compliance,
        "overall_compliant": all([
            all(item["compliant"] for item in facility_compliance.values()),
            len(per_diem_warnings) == 0,
            all(item["compliant"] for item in far_compliance.values()),
            all(item["compliant"] for item in ipp_compliance.values())
        ])
    }

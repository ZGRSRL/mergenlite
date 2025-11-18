from typing import Dict, Any, List
from ...schemas import Requirement, Evidence


def get_extraction_prompt(text: str, document_type: str) -> str:
    """Get prompt for extracting structured data from document"""
    
    if document_type == "rfq":
        return f"""
        Analyze the following RFQ document and extract requirements in JSON format.
        
        Document text:
        {text}
        
        Extract the following information:
        1. General requirements (capacity, dates, location)
        2. Lodging room requirements
        3. Conference room requirements
        4. AV/Boardroom requirements
        5. Schedule/Block requirements
        6. Invoicing requirements (IPP, per-diem)
        7. FAR clauses (52.204-24, 52.204-25, 52.204-26)
        
        Return JSON with this structure:
        {{
            "requirements": [
                {{
                    "code": "R-001",
                    "text": "Requirement description",
                    "category": "capacity|date|transport|av|invoice|clauses",
                    "priority": "low|medium|high|critical"
                }}
            ],
            "dates": ["2024-04-14", "2024-04-15"],
            "capacity": 100,
            "location": "Orlando, FL",
            "per_diem_limit": 140.0
        }}
        """
    
    elif document_type == "facility":
        return f"""
        Analyze the following facility document and extract features in JSON format.
        
        Document text:
        {text}
        
        Extract the following information:
        1. Shuttle service availability
        2. Wi-Fi internet access
        3. Parking facilities
        4. Breakout rooms (count and capacity)
        5. Boardroom availability
        6. AV equipment list
        7. Restaurant distance or shuttle service
        8. Airport distance
        
        Return JSON with this structure:
        {{
            "features": [
                {{
                    "name": "shuttle",
                    "value": "Free airport shuttle service available",
                    "confidence": 0.9
                }}
            ],
            "room_capacity": {{
                "main_room": 100,
                "breakout_room": 15,
                "boardroom": 20
            }},
            "distance_info": {{
                "airport_distance": 5.2,
                "restaurant_distance": 0.1
            }},
            "av_equipment": ["projector", "microphone", "screen"]
        }}
        """
    
    elif document_type == "past_performance":
        return f"""
        Analyze the following past performance document and extract project information.
        
        Document text:
        {text}
        
        Extract the following information:
        1. Project titles and descriptions
        2. Client names
        3. Contract values
        4. Project periods
        5. Scope of work
        6. Contact information (POC, email, phone)
        7. Participant counts
        8. Similar project keywords
        
        Return JSON with this structure:
        {{
            "performances": [
                {{
                    "title": "Project title",
                    "client": "Client name",
                    "value": 50000.0,
                    "period": "2022-2023",
                    "scope": "Project description",
                    "participant_count": 75
                }}
            ],
            "contact_info": {{
                "poc": "Contact person",
                "email": "email@example.com",
                "phone": "+1-555-123-4567"
            }},
            "scope_keywords": ["conference", "seminar", "meeting"]
        }}
        """
    
    else:
        return f"""
        Analyze the following document and extract relevant information.
        
        Document text:
        {text}
        
        Extract key information and return as JSON.
        """


def get_technical_approach_prompt(
    requirement: Requirement,
    evidence: List[Evidence],
    facility_features: List[Dict[str, Any]],
    past_performance: List[Dict[str, Any]]
) -> str:
    """Get prompt for generating technical approach section"""
    
    evidence_text = "\n".join([f"- {e.snippet}" for e in evidence])
    facility_text = "\n".join([f"- {f['name']}: {f['value']}" for f in facility_features])
    past_perf_text = "\n".join([f"- {p['title']}: {p['scope']}" for p in past_performance])
    
    return f"""
    Write a technical approach section for the following requirement:
    
    Requirement: {requirement.text}
    Category: {requirement.category}
    
    Evidence found:
    {evidence_text}
    
    Facility features available:
    {facility_text}
    
    Past performance examples:
    {past_perf_text}
    
    Write a professional technical approach that:
    1. Addresses the specific requirement
    2. References the evidence and facility features
    3. Demonstrates capability through past performance
    4. Shows understanding of the requirement
    5. Is 2-3 paragraphs long
    
    Use a professional, confident tone suitable for a government proposal.
    """


def get_executive_summary_prompt(
    rfq_title: str,
    compliance_matrix: Dict[str, Any],
    key_risks: List[str],
    mitigation_strategies: List[str]
) -> str:
    """Get prompt for generating executive summary"""
    
    return f"""
    Write an executive summary for a government proposal with the following information:
    
    RFQ Title: {rfq_title}
    
    Compliance Status:
    - Total Requirements: {compliance_matrix.get('total_requirements', 0)}
    - Met Requirements: {compliance_matrix.get('met_requirements', 0)}
    - Gap Requirements: {compliance_matrix.get('gap_requirements', 0)}
    - Overall Risk: {compliance_matrix.get('overall_risk', 'unknown')}
    
    Key Risks:
    {chr(10).join([f"- {risk}" for risk in key_risks])}
    
    Mitigation Strategies:
    {chr(10).join([f"- {strategy}" for strategy in mitigation_strategies])}
    
    Write a compelling executive summary that:
    1. Highlights our understanding of the requirements
    2. Demonstrates our capability and experience
    3. Addresses key risks and mitigation strategies
    4. Shows confidence in our ability to deliver
    5. Is 3-4 paragraphs long
    
    Use a professional, confident tone suitable for government contracting.
    """


def get_past_performance_prompt(
    past_performance: List[Dict[str, Any]],
    requirement_text: str
) -> str:
    """Get prompt for generating past performance section"""
    
    perf_text = "\n".join([
        f"- {p['title']} for {p['client']} ({p['period']}): {p['scope']}"
        for p in past_performance
    ])
    
    return f"""
    Write a past performance section that demonstrates our capability for this requirement:
    
    Requirement: {requirement_text}
    
    Relevant Past Performance:
    {perf_text}
    
    Write a past performance section that:
    1. Selects the most relevant examples
    2. Shows similarity to the current requirement
    3. Highlights successful outcomes
    4. Demonstrates scale and complexity
    5. Is 2-3 paragraphs long
    
    Use a professional tone that emphasizes our track record of success.
    """


def get_pricing_summary_prompt(
    pricing_items: List[Dict[str, Any]],
    total_cost: float,
    per_diem_compliance: bool
) -> str:
    """Get prompt for generating pricing summary"""
    
    items_text = "\n".join([
        f"- {item['name']}: {item['qty']} {item['unit']} @ ${item['unit_price']:.2f} = ${item['total_price']:.2f}"
        for item in pricing_items
    ])
    
    compliance_text = "compliant with per-diem limits" if per_diem_compliance else "requires per-diem waiver"
    
    return f"""
    Write a pricing summary section with the following information:
    
    Pricing Items:
    {items_text}
    
    Total Cost: ${total_cost:.2f}
    Per-Diem Compliance: {compliance_text}
    
    Write a pricing summary that:
    1. Explains our pricing approach
    2. Highlights value for money
    3. Addresses per-diem compliance
    4. Shows transparency in pricing
    5. Is 2-3 paragraphs long
    
    Use a professional tone that emphasizes value and compliance.
    """


def get_compliance_matrix_prompt(
    requirements: List[Requirement],
    evidence: List[Evidence]
) -> str:
    """Get prompt for generating compliance matrix"""
    
    return f"""
    Generate a compliance matrix for the following requirements:
    
    Requirements:
    {chr(10).join([f"- {req.code}: {req.text}" for req in requirements])}
    
    Available Evidence:
    {chr(10).join([f"- {ev.snippet}" for ev in evidence])}
    
    For each requirement, determine:
    1. Whether we meet the requirement (Yes/No/Partial)
    2. How we meet it (specific evidence)
    3. Risk level (Low/Medium/High/Critical)
    4. Any gaps or concerns
    
    Return as a structured format suitable for a compliance matrix table.
    """

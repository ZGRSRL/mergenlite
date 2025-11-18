import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def extract_requirements_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract requirements from RFQ text"""
    requirements = []
    
    # Common RFQ section patterns
    section_patterns = [
        r"General Requirements?",
        r"Lodging Room Requirements?",
        r"Conference Room Requirements?",
        r"AV/Boardroom Requirements?",
        r"Schedule/Block Requirements?",
        r"Invoicing Requirements?",
        r"FAR Clauses?",
        r"52\.204-24",
        r"52\.204-25",
        r"52\.204-26"
    ]
    
    # Requirement item patterns
    item_patterns = [
        r"^\d+[\.\)]\s+(.+?)(?=\n\d+[\.\)]|\n\n|$)",
        r"^[•\-\*]\s+(.+?)(?=\n[•\-\*]|\n\n|$)",
        r"^[a-z][\.\)]\s+(.+?)(?=\n[a-z][\.\)]|\n\n|$)"
    ]
    
    lines = text.split('\n')
    current_section = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check for section headers
        for pattern in section_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                current_section = line
                break
        
        # Check for requirement items
        if current_section:
            for pattern in item_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    requirement_text = match.group(1).strip()
                    if len(requirement_text) > 10:  # Filter out very short items
                        requirements.append({
                            "text": requirement_text,
                            "section": current_section,
                            "line_number": i + 1
                        })
                    break
    
    return requirements


def categorize_requirement(text: str) -> str:
    """Categorize a requirement based on its content"""
    text_lower = text.lower()
    
    # Capacity requirements
    if any(word in text_lower for word in ['capacity', 'participants', 'attendees', 'people', 'guests']):
        return "capacity"
    
    # Date/time requirements
    if any(word in text_lower for word in ['date', 'time', 'schedule', 'duration', 'april', 'may', 'june']):
        return "date"
    
    # Transportation requirements
    if any(word in text_lower for word in ['shuttle', 'transportation', 'airport', 'pickup', 'drop']):
        return "transport"
    
    # AV requirements
    if any(word in text_lower for word in ['av', 'audio', 'visual', 'microphone', 'projector', 'screen']):
        return "av"
    
    # Lodging requirements
    if any(word in text_lower for word in ['room', 'lodging', 'hotel', 'accommodation', 'overnight']):
        return "lodging"
    
    # Invoice requirements
    if any(word in text_lower for word in ['invoice', 'billing', 'payment', 'ipp', 'per diem']):
        return "invoice"
    
    # FAR clauses
    if any(word in text_lower for word in ['far', '52.204', 'representation', 'certification']):
        return "clauses"
    
    return "other"


def extract_dates_from_text(text: str) -> List[str]:
    """Extract dates from text"""
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{2,4}\b',  # Month DD, YYYY
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{2,4}\b'  # Month DD, YYYY
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    
    return dates


def extract_capacity_from_text(text: str) -> int:
    """Extract capacity/participant count from text"""
    capacity_patterns = [
        r'(\d+)\s+(?:participants?|attendees?|people|guests?)',
        r'capacity\s+of\s+(\d+)',
        r'up\s+to\s+(\d+)',
        r'(\d+)\s+person'
    ]
    
    for pattern in capacity_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return 0


def process_rfq_document(text: str) -> Dict[str, Any]:
    """Process RFQ document and extract structured data"""
    logger.info("Processing RFQ document")
    
    # Extract requirements
    requirements = extract_requirements_from_text(text)
    
    # Categorize requirements
    for req in requirements:
        req['category'] = categorize_requirement(req['text'])
    
    # Extract dates
    dates = extract_dates_from_text(text)
    
    # Extract capacity
    capacity = extract_capacity_from_text(text)
    
    # Extract per-diem information
    per_diem_pattern = r'\$(\d+(?:\.\d{2})?)'
    per_diem_matches = re.findall(per_diem_pattern, text)
    per_diem_amounts = [float(amount) for amount in per_diem_matches]
    
    return {
        "requirements": requirements,
        "dates": dates,
        "capacity": capacity,
        "per_diem_amounts": per_diem_amounts,
        "total_requirements": len(requirements)
    }




"""
Seating Chart Parser
Extracts structured seating layout from PDF seating charts.
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)

try:
    from ..parsing.pdf_utils import extract_text_from_pdf
    PDF_UTILS_AVAILABLE = True
except ImportError:
    PDF_UTILS_AVAILABLE = False
    logger.warning("PDF utils not available for seating chart parser")


def parse_seating_chart_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Parse seating chart PDF and extract structured layout.
    
    Args:
        pdf_path: Path to seating chart PDF file
        
    Returns:
        Dict with structured seating layout:
        {
            "hollow_square": {"capacity_min": int, "capacity_max": int, "location": str},
            "classroom": [{"location": str, "capacity": int}],
            "theater": {"capacity": int, "location": str},
            "special_areas": [
                {"name": "Tech Team", "location": str},
                {"name": "AV Team", "location": str},
                {"name": "Court Reporter", "location": str},
                {"name": "Confidence Monitor", "location": str},
            ],
            "power_requirements": {"extension_cords": bool, "power_strips": bool, "notes": str}
        }
    """
    if not PDF_UTILS_AVAILABLE:
        logger.warning("PDF utils not available, cannot parse seating chart")
        return {}
    
    if not Path(pdf_path).exists():
        logger.error(f"Seating chart PDF not found: {pdf_path}")
        return {}
    
    try:
        # Extract text from PDF
        text = extract_text_from_pdf(pdf_path)
        if not text:
            logger.warning(f"No text extracted from seating chart PDF: {pdf_path}")
            return {}
        
        # Parse using keyword-based approach
        result = {
            "hollow_square": None,
            "classroom": [],
            "theater": None,
            "special_areas": [],
            "power_requirements": None,
        }
        
        text_lower = text.lower()
        
        # Parse Hollow Square
        hollow_square_patterns = [
            r"hollow\s+square[:\s]+(\d+)[\s-]+(\d+)",  # "Hollow Square: 25-28"
            r"hollow\s+square[:\s]+(\d+)\s*participants?",  # "Hollow Square: 25 participants"
        ]
        for pattern in hollow_square_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    result["hollow_square"] = {
                        "capacity_min": int(match.group(1)),
                        "capacity_max": int(match.group(2)),
                        "location": "Main area",
                    }
                else:
                    capacity = int(match.group(1))
                    result["hollow_square"] = {
                        "capacity_min": capacity,
                        "capacity_max": capacity,
                        "location": "Main area",
                    }
                break
        
        # Parse Classroom
        classroom_patterns = [
            r"classroom[:\s]+(?:right|left|bottom|top)[\s,]+(\d+)",  # "Classroom right, 20"
            r"classroom[:\s]+(\d+)\s*participants?",  # "Classroom: 20 participants"
        ]
        for pattern in classroom_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                location_match = re.search(r"(right|left|bottom|top)", text_lower[match.start():match.end()+50], re.IGNORECASE)
                location = location_match.group(1) if location_match else "TBD"
                capacity = int(match.group(1))
                result["classroom"].append({
                    "location": location,
                    "capacity": capacity,
                })
        
        # Parse Theater
        theater_patterns = [
            r"theater[:\s]+(?:approx\.?|approximately)?\s*(\d+)",  # "Theater: Approx. 20"
            r"theater[:\s]+(\d+)\s*participants?",  # "Theater: 20 participants"
        ]
        for pattern in theater_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                capacity = int(match.group(1))
                result["theater"] = {
                    "capacity": capacity,
                    "location": "Main area",
                }
                break
        
        # Parse Special Areas
        special_areas = [
            "tech team",
            "av team",
            "court reporter",
            "confidence monitor",
            "water",
            "charging",
        ]
        for area in special_areas:
            pattern = rf"{area}[:\s]+([^,\n]+)"
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                result["special_areas"].append({
                    "name": area.title(),
                    "location": location,
                })
        
        # Parse Power Requirements
        power_keywords = ["extension cord", "power strip", "power outlet", "electrical"]
        power_notes = []
        for keyword in power_keywords:
            if keyword in text_lower:
                # Find context around keyword
                idx = text_lower.find(keyword)
                context = text[max(0, idx-50):idx+100]
                power_notes.append(context.strip())
        
        if power_notes:
            result["power_requirements"] = {
                "extension_cords": "extension cord" in text_lower,
                "power_strips": "power strip" in text_lower,
                "notes": "; ".join(power_notes),
            }
        
        logger.info(f"Parsed seating chart: {len(result['classroom'])} classrooms, {len(result['special_areas'])} special areas")
        return result
        
    except Exception as e:
        logger.error(f"Error parsing seating chart PDF {pdf_path}: {e}", exc_info=True)
        return {}


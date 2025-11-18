import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def extract_past_performance_info(text: str) -> List[Dict[str, Any]]:
    """Extract past performance information from text"""
    performances = []
    
    # Common patterns for past performance
    performance_patterns = [
        r'project\s+title[:\s]+(.+?)(?=\n|client|value|period)',
        r'client[:\s]+(.+?)(?=\n|project|value|period)',
        r'contract\s+value[:\s]+\$?([\d,]+(?:\.\d{2})?)',
        r'period[:\s]+(.+?)(?=\n|client|project|value)',
        r'description[:\s]+(.+?)(?=\n\n|\nclient|\nproject)'
    ]
    
    # Split text into sections (assuming each performance is separated by double newlines)
    sections = re.split(r'\n\s*\n', text)
    
    for section in sections:
        if len(section.strip()) < 50:  # Skip very short sections
            continue
            
        performance = {}
        
        # Extract project title
        title_match = re.search(r'project\s+title[:\s]+(.+?)(?=\n|client|value|period)', section, re.IGNORECASE)
        if title_match:
            performance['title'] = title_match.group(1).strip()
        
        # Extract client
        client_match = re.search(r'client[:\s]+(.+?)(?=\n|project|value|period)', section, re.IGNORECASE)
        if client_match:
            performance['client'] = client_match.group(1).strip()
        
        # Extract contract value
        value_match = re.search(r'contract\s+value[:\s]+\$?([\d,]+(?:\.\d{2})?)', section, re.IGNORECASE)
        if value_match:
            value_str = value_match.group(1).replace(',', '')
            performance['value'] = float(value_str)
        
        # Extract period
        period_match = re.search(r'period[:\s]+(.+?)(?=\n|client|project|value)', section, re.IGNORECASE)
        if period_match:
            performance['period'] = period_match.group(1).strip()
        
        # Extract description/scope
        desc_match = re.search(r'description[:\s]+(.+?)(?=\n\n|\nclient|\nproject)', section, re.IGNORECASE | re.DOTALL)
        if desc_match:
            performance['scope'] = desc_match.group(1).strip()
        
        # If we found at least a title, add this performance
        if 'title' in performance:
            performances.append(performance)
    
    return performances


def extract_contact_info(text: str) -> Dict[str, str]:
    """Extract contact information (POC, phone, email)"""
    contact_info = {}
    
    # Email pattern
    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)
    if email_match:
        contact_info['email'] = email_match.group(1)
    
    # Phone pattern
    phone_match = re.search(r'(\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})', text)
    if phone_match:
        contact_info['phone'] = phone_match.group(1)
    
    # POC pattern
    poc_patterns = [
        r'point\s+of\s+contact[:\s]+(.+?)(?=\n|email|phone)',
        r'poc[:\s]+(.+?)(?=\n|email|phone)',
        r'contact\s+person[:\s]+(.+?)(?=\n|email|phone)'
    ]
    
    for pattern in poc_patterns:
        poc_match = re.search(pattern, text, re.IGNORECASE)
        if poc_match:
            contact_info['poc'] = poc_match.group(1).strip()
            break
    
    return contact_info


def extract_scope_keywords(text: str) -> List[str]:
    """Extract keywords that describe the scope of work"""
    scope_keywords = []
    
    # Common scope keywords
    keyword_patterns = [
        r'conference',
        r'seminar',
        r'meeting',
        r'event',
        r'training',
        r'workshop',
        r'convention',
        r'summit',
        r'retreat',
        r'gala',
        r'banquet',
        r'networking',
        r'presentation',
        r'demonstration',
        r'exhibition',
        r'trade\s+show'
    ]
    
    text_lower = text.lower()
    
    for pattern in keyword_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            scope_keywords.append(pattern.replace(r'\s+', ' '))
    
    return scope_keywords


def extract_participant_count(text: str) -> int:
    """Extract participant count from past performance"""
    participant_patterns = [
        r'(\d+)\s+participants?',
        r'(\d+)\s+attendees?',
        r'(\d+)\s+people',
        r'(\d+)\s+guests?',
        r'capacity\s+of\s+(\d+)',
        r'up\s+to\s+(\d+)'
    ]
    
    for pattern in participant_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    
    return 0


def process_past_performance_document(text: str) -> Dict[str, Any]:
    """Process past performance document and extract structured data"""
    logger.info("Processing past performance document")
    
    # Extract past performance information
    performances = extract_past_performance_info(text)
    
    # Extract contact information
    contact_info = extract_contact_info(text)
    
    # Extract scope keywords
    scope_keywords = extract_scope_keywords(text)
    
    # Extract participant count
    participant_count = extract_participant_count(text)
    
    return {
        "performances": performances,
        "contact_info": contact_info,
        "scope_keywords": scope_keywords,
        "participant_count": participant_count,
        "total_performances": len(performances)
    }




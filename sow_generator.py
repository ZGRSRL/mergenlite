#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SOW Generator - Otellere Yazışma İçin
RFQ analizinden Sample SOW formatına göre Statement of Work oluşturur
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from document_processor import DocumentProcessor
from llm_analyzer import LLMAnalyzer

logger = logging.getLogger(__name__)

def _parse_start_date(date_range: str) -> str:
    """Date range'den start date'i parse et"""
    if not date_range or date_range == 'TBD':
        return 'TBD'
    
    # "March 3-6, 2026" formatı
    match = re.search(r'(\w+\s+\d+)[-\s]+(\d+),\s*(\d{4})', date_range)
    if match:
        month_day = match.group(1)
        year = match.group(3)
        return f"{month_day}, {year}"
    
    # "March 3, 2026 to March 6, 2026" formatı
    if ' to ' in date_range:
        start_part = date_range.split(' to ')[0].strip()
        return start_part
    
    # "2024-03-01 to 2024-03-05" formatı
    if re.match(r'\d{4}-\d{2}-\d{2}', date_range.split(' to ')[0] if ' to ' in date_range else date_range):
        start_part = date_range.split(' to ')[0].strip() if ' to ' in date_range else date_range
        try:
            dt = datetime.strptime(start_part, '%Y-%m-%d')
            return dt.strftime('%B %d, %Y')
        except:
            return start_part
    
    # "March 3, 2026" formatı
    return date_range.split('-')[0].strip() if '-' in date_range else date_range.strip()

def _parse_end_date(date_range: str) -> str:
    """Date range'den end date'i parse et"""
    if not date_range or date_range == 'TBD':
        return 'TBD'
    
    # "March 3-6, 2026" formatı
    match = re.search(r'(\w+)\s+\d+[-\s]+(\d+),\s*(\d{4})', date_range)
    if match:
        month = match.group(1)
        end_day = match.group(2)
        year = match.group(3)
        return f"{month} {end_day}, {year}"
    
    # "March 3, 2026 to March 6, 2026" formatı
    if ' to ' in date_range:
        end_part = date_range.split(' to ')[-1].strip()
        return end_part
    
    # "2024-03-01 to 2024-03-05" formatı
    if re.match(r'\d{4}-\d{2}-\d{2}', date_range.split(' to ')[-1] if ' to ' in date_range else date_range):
        end_part = date_range.split(' to ')[-1].strip() if ' to ' in date_range else date_range
        try:
            dt = datetime.strptime(end_part, '%Y-%m-%d')
            return dt.strftime('%B %d, %Y')
        except:
            return end_part
    
    # Tek tarih varsa aynısını döndür
    return date_range.strip()

def load_sample_sow_template() -> str:
    """Sample SOW formatını yükle"""
    sample_sow_path = Path("samples") / "SAMPLE SOW FOR CHTGPT.pdf"
    
    if not sample_sow_path.exists():
        logger.warning("Sample SOW not found, using default template")
        return get_default_sow_template()
    
    try:
        processor = DocumentProcessor()
        result = processor.process_file_from_path(str(sample_sow_path))
        
        if result.get('success'):
            return result['data'].get('text', '')
        else:
            logger.warning(f"Failed to load sample SOW: {result.get('error')}")
            return get_default_sow_template()
    except Exception as e:
        logger.error(f"Error loading sample SOW: {e}", exc_info=True)
        return get_default_sow_template()

def get_default_sow_template() -> str:
    """Varsayılan SOW şablonu"""
    return """
STATEMENT OF WORK (SOW)
FOR HOTEL ACCOMMODATIONS AND MEETING SPACE

1. BACKGROUND
[Project background and purpose]

2. SCOPE OF WORK
2.1 Lodging Requirements
- Room block requirements
- Room types and quantities
- Check-in/check-out dates
- Special accommodations (ADA, etc.)

2.2 Meeting Space Requirements
- Conference room requirements
- AV equipment needs
- Setup requirements
- Capacity requirements

2.3 Additional Services
- Shuttle services
- Parking
- F&B requirements
- Other services

3. DELIVERABLES
[List of deliverables]

4. PERIOD OF PERFORMANCE
[Start date] through [End date]

5. LOCATION
[City, State, Address]

6. TERMS AND CONDITIONS
[Payment terms, cancellation policy, etc.]

7. COMPLIANCE REQUIREMENTS
- FAR clauses
- Tax exemption
- IPP invoicing
- Other compliance items
"""

def generate_sow_from_rfq_analysis(
    rfq_analysis: Dict[str, Any],
    opportunity_info: Optional[Dict[str, Any]] = None,
    vendor_profile: Optional[Dict[str, Any]] = None,
    output_folder: Optional[str] = None
) -> Dict[str, str]:
    """
    RFQ analizinden otellere yazışma için SOW oluştur
    
    Args:
        rfq_analysis: RFQ analiz sonuçları (opportunity_requirements_report)
        opportunity_info: Fırsat bilgileri
        vendor_profile: Vendor profile bilgileri
    
    Returns:
        SOW metni (Markdown formatında)
    """
    # Sample SOW formatını yükle
    sample_template = load_sample_sow_template()
    
    # RFQ analiz verilerini hazırla
    analysis_json = json.dumps(rfq_analysis, ensure_ascii=False, indent=2)
    opp_info_json = json.dumps(opportunity_info or {}, ensure_ascii=False, indent=2)
    vendor_json = json.dumps(vendor_profile or {}, ensure_ascii=False, indent=2)
    
    system_message = """
You are a Statement of Work (SOW) writing expert. You are preparing a professional SOW to be sent to hotels using RFQ analysis results.

IMPORTANT RULES:
1. NEVER use government contact information (name, email, phone, address) from the RFQ
2. Follow the Sample SOW format
3. Specify all requirements clearly and in detail
4. Write in language that hotel management will understand
5. Always include critical information such as dates, room count, capacity
6. Mention FAR clauses and compliance requirements but you don't need to go into details

Output: Professional SOW text in Markdown format following the Sample SOW format. Return only the SOW text, no other explanations.
"""
    
    user_prompt = f"""
Using the RFQ analysis results below, prepare a Statement of Work (SOW) to be sent to hotels.

SAMPLE SOW FORMAT:
{sample_template[:2000]}

RFQ ANALYSIS RESULTS:
{analysis_json[:6000]}

OPPORTUNITY INFORMATION:
{opp_info_json}

VENDOR PROFILE:
{vendor_json}

Please follow the sample SOW format above and extract all requirements from the RFQ analysis results to create a professional SOW.

IMPORTANT:
- Include all date, room, capacity, location information
- Specify meeting space requirements in detail
- Explain AV requirements
- State compliance requirements
- Use clear language that hotel management will understand
- DO NOT USE government contact information
"""
    
    try:
        # OpenAI API ile SOW oluştur
        import os
        import openai
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.warning("OpenAI API key not found, using fallback SOW")
            return create_simple_sow(rfq_analysis, opportunity_info, vendor_profile)
        
        openai.api_key = api_key
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        sow_text = response.choices[0].message.content.strip()
        
        # Markdown code block varsa temizle
        if sow_text.startswith("```"):
            lines = sow_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines[-1].strip() == "```":
                lines = lines[:-1]
            sow_text = '\n'.join(lines)
        
        if not sow_text or len(sow_text) < 100:
            # Fallback: Basit SOW oluştur
            sow_text = create_simple_sow(rfq_analysis, opportunity_info, vendor_profile)
        
        logger.info(f"[SOW Generator] Generated SOW ({len(sow_text)} chars)")
        
        # SOW'u kaydet ve PDF oluştur
        sow_md_path = None
        sow_pdf_path = None
        
        if output_folder:
            folder = Path(output_folder)
            folder.mkdir(parents=True, exist_ok=True)
            
            # Markdown kaydet
            sow_md_path = folder / "sow.md"
            sow_md_path.write_text(sow_text, encoding='utf-8')
            logger.info(f"[SOW Generator] Saved Markdown: {sow_md_path}")
            
            # PDF oluştur
            try:
                from sow_pdf_generator import convert_sow_md_to_pdf
                sow_pdf_path = convert_sow_md_to_pdf(str(sow_md_path))
                logger.info(f"[SOW Generator] Generated PDF: {sow_pdf_path}")
            except Exception as e:
                logger.warning(f"[SOW Generator] PDF generation failed: {e}")
        
        return {
            'markdown': sow_text,
            'markdown_path': str(sow_md_path) if sow_md_path else None,
            'pdf_path': str(sow_pdf_path) if sow_pdf_path else None
        }
        
    except ImportError:
        logger.warning("OpenAI not available, using fallback SOW")
        sow_text = create_simple_sow(rfq_analysis, opportunity_info, vendor_profile)
        return _save_sow_files(sow_text, output_folder)
    except Exception as e:
        logger.error(f"[SOW Generator] Error: {e}", exc_info=True)
        # Fallback: Basit SOW oluştur
        sow_text = create_simple_sow(rfq_analysis, opportunity_info, vendor_profile)
        return _save_sow_files(sow_text, output_folder)

def _save_sow_files(sow_text: str, output_folder: Optional[str] = None) -> Dict[str, Optional[str]]:
    """SOW metnini kaydet ve PDF oluştur"""
    sow_md_path = None
    sow_pdf_path = None
    
    if output_folder:
        folder = Path(output_folder)
        folder.mkdir(parents=True, exist_ok=True)
        
        # Markdown kaydet
        sow_md_path = folder / "sow.md"
        sow_md_path.write_text(sow_text, encoding='utf-8')
        logger.info(f"[SOW Generator] Saved Markdown: {sow_md_path}")
        
        # PDF oluştur
        try:
            from sow_pdf_generator import convert_sow_md_to_pdf
            sow_pdf_path = convert_sow_md_to_pdf(str(sow_md_path))
            logger.info(f"[SOW Generator] Generated PDF: {sow_pdf_path}")
        except Exception as e:
            logger.warning(f"[SOW Generator] PDF generation failed: {e}")
    
    return {
        'markdown': sow_text,
        'markdown_path': str(sow_md_path) if sow_md_path else None,
        'pdf_path': str(sow_pdf_path) if sow_pdf_path else None
    }

def create_simple_sow(
    rfq_analysis: Dict[str, Any],
    opportunity_info: Optional[Dict[str, Any]] = None,
    vendor_profile: Optional[Dict[str, Any]] = None
) -> str:
    """Basit SOW oluştur (fallback)"""
    
    # RFQ analizinden bilgileri çıkar
    opp_info = rfq_analysis.get('opportunity_info', {})
    event_req = rfq_analysis.get('event_requirements', {})
    commercial = rfq_analysis.get('commercial_terms', {})
    compliance = rfq_analysis.get('compliance', {})
    
    # Vendor bilgileri
    vendor_name = vendor_profile.get('company_name', 'CREATA GLOBAL MEETING & EVENTS') if vendor_profile else 'CREATA GLOBAL MEETING & EVENTS'
    
    sow = f"""# STATEMENT OF WORK (SOW)
## FOR HOTEL ACCOMMODATIONS AND MEETING SPACE

### 1. BACKGROUND

This Statement of Work (SOW) outlines the requirements for hotel accommodations and meeting space services for a federal government event.

**Solicitation Number:** {opp_info.get('solicitation_number', 'N/A')}
**Agency:** {opp_info.get('agency', 'N/A')}
**Event Title:** {opp_info.get('title', 'N/A')}

### 2. SCOPE OF WORK

#### 2.1 Lodging Requirements

**Location:** {event_req.get('location', 'TBD')}
**Date Range:** {event_req.get('date_range', 'TBD')}
**Room Block:** {event_req.get('room_block_plan', 'TBD')}

**Participant Capacity:**
- Minimum: {event_req.get('participants_min', 'N/A')}
- Target: {event_req.get('participants_target', 'N/A')}

**Special Requirements:**
- ADA compliant rooms required
- Room types as specified in RFQ

#### 2.2 Meeting Space Requirements

**Meeting Spaces:**
{event_req.get('meeting_spaces', 'TBD')}

**AV Requirements:**
{event_req.get('av_requirements', 'TBD')}

**Capacity:** {event_req.get('participants_target', 'N/A')} participants

#### 2.3 Additional Services

**Special Logistics:**
{event_req.get('special_logistics', 'TBD')}

**F&B Requirements:**
{event_req.get('fnb_requirements', 'TBD')}

### 3. DELIVERABLES

- Hotel room block as specified
- Meeting/conference space with required capacity
- AV equipment and setup
- Shuttle services (if required)
- Parking arrangements
- F&B services (if required)

### 4. PERIOD OF PERFORMANCE

**Start Date:** {_parse_start_date(event_req.get('date_range', ''))}
**End Date:** {_parse_end_date(event_req.get('date_range', ''))}

### 5. LOCATION

{event_req.get('location', 'TBD')}

### 6. TERMS AND CONDITIONS

**Estimated Value:** {commercial.get('estimated_value') or 'To be determined based on final room block and services'}
**Payment Terms:** {commercial.get('payment_terms') or 'Net 30 days, subject to contract terms'}
**Tax Exempt:** Yes  # Federal government contracts are tax exempt
**E-Invoicing (IPP):** Required  # Federal contracts require IPP invoicing

**Cancellation Policy:**
{commercial.get('cancellation_penalties', 'Per contract terms')}

### 7. COMPLIANCE REQUIREMENTS

**FAR Clauses:**
- FAR 52.212-4: {'Required' if compliance.get('far_52_212_4', False) else 'Not Required'}
- FAR 52.212-5: {'Required' if compliance.get('far_52_212_5', False) else 'Not Required'}
- FAR 52.204-24/25/26: {'Required' if compliance.get('far_52_204_24_25_26', False) else 'Not Required'}

**Other Compliance:**
{', '.join(compliance.get('other_mandatory_clauses', [])) if compliance.get('other_mandatory_clauses') else 'Per RFQ requirements'}

### 8. VENDOR INFORMATION

**Company:** {vendor_name}
**SAM.gov Registered:** {'Yes' if vendor_profile and vendor_profile.get('sam_registered', False) else 'Yes (to be confirmed)'}
**UEI:** {vendor_profile.get('uei', 'To be provided') if vendor_profile else 'To be provided'}
**DUNS:** {vendor_profile.get('duns', 'To be provided') if vendor_profile else 'To be provided'}

---

**Prepared by:** {vendor_name}
**Date:** {datetime.now().strftime('%B %d, %Y')}
"""
    
    return sow


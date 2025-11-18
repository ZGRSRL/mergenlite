#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vendor Profile Extractor
PDF'den şirket bilgileri ve past performance çıkarır
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from document_processor import DocumentProcessor
from llm_analyzer import LLMAnalyzer
from llm_client import (
    call_logged_llm,
    extract_message_text,
    LLMNotAvailableError,
)

logger = logging.getLogger(__name__)

def extract_vendor_profile_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    PDF'den vendor profile bilgilerini çıkar
    
    Args:
        pdf_path: Past performance PDF dosyasının yolu
    
    Returns:
        Vendor profile dictionary
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    # PDF'den metin çıkar
    processor = DocumentProcessor()
    result = processor.process_file_from_path(str(pdf_file))
    
    if not result.get('success'):
        raise ValueError(f"Failed to extract text from PDF: {result.get('error')}")
    
    pdf_text = result['data'].get('text', '')
    if not pdf_text:
        raise ValueError("No text extracted from PDF")
    
    logger.info(f"[Vendor Profile] Extracted {len(pdf_text)} characters from PDF")
    
    # LLM ile vendor profile çıkar
    llm_analyzer = LLMAnalyzer()
    
    system_message = """
You are a vendor profile extraction expert. You extract company information and past performance information from PDF content.

Information to extract:
1. Company Name
2. Address
3. UEI (Unique Entity Identifier)
4. DUNS (Data Universal Numbering System)
5. SAM.gov registration status
6. Contact information (email, phone, contact person name)
7. Past Performance (previous projects, clients, achievements)

Output format (JSON):
{
  "company_name": "...",
  "address": "...",
  "uei": "...",
  "duns": "...",
  "sam_registered": true/false,
  "contact": {
    "name": "...",
    "email": "...",
    "phone": "..."
  },
  "past_performance": [
    "Project 1 description",
    "Project 2 description",
    ...
  ]
}

Return ONLY JSON, no other explanations.
"""
    
    user_prompt = f"""
Extract vendor profile information from the PDF content below:

{pdf_text[:8000]}  # First 8000 characters (for LLM limit)
"""
    
    try:
        response = call_logged_llm(
            agent_name="VendorProfileExtractor",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=2000,
        )
        result_text = extract_message_text(response).strip()
        
        # JSON parse et
        try:
            # JSON code block varsa temizle
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            extracted_data = json.loads(result_text)
        except:
            # JSON bulmaya çalış
            import re
            json_match = re.search(r'\{[\s\S]*\}', result_text)
            if json_match:
                extracted_data = json.loads(json_match.group(0))
            else:
                raise ValueError("No valid JSON found in response")
        
        logger.info(f"[Vendor Profile] Extracted vendor profile: {extracted_data.get('company_name', 'N/A')}")
        return extracted_data
        
    except LLMNotAvailableError as exc:
        logger.warning(f"LLM not available, using fallback vendor profile: {exc}")
        return _get_fallback_vendor_profile()
    except Exception as e:
        logger.error(f"[Vendor Profile] Extraction error: {e}", exc_info=True)
        # Fallback: Basit bilgileri çıkar
        return _get_fallback_vendor_profile()

def _get_fallback_vendor_profile() -> Dict[str, Any]:
    """Fallback vendor profile"""
    return {
        "company_name": "CREATA GLOBAL MEETING & EVENTS",
        "address": "",
        "uei": "",
        "duns": "",
        "sam_registered": True,
        "contact": {
            "name": "",
            "email": "",
            "phone": ""
        },
        "past_performance": []
    }


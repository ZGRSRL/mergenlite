#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Proposal Pipeline
Analiz sonuçlarından otomatik teklif taslağı üretir
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(dotenv_path='mergen/.env')

logger = logging.getLogger(__name__)

# AutoGen import
try:
    from autogen import ConversableAgent
    AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False
    logger.warning("AutoGen not available, proposal generation will be limited")

# Local imports
try:
    from agents.proposal_generator_agent import make_proposal_generator_agent
except ImportError:
    # Fallback: define inline
    def make_proposal_generator_agent(llm_config):
        if not AUTOGEN_AVAILABLE or not llm_config:
            return None
        
        system_message = """
You are a "Federal Proposal Writer" agent. You are preparing a professional proposal draft using Opportunity_Requirements_Report data.

IMPORTANT: NEVER use government contact information (name, email, phone, address) from the RFQ.

Only use the following information:
- Opportunity_Requirements_Report content
- Vendor profile information
- Technical requirements from the analysis

Output: Professional proposal draft in Markdown format.
"""
        return ConversableAgent(
            name="proposal_generator",
            system_message=system_message,
            llm_config=llm_config,
            max_consecutive_auto_reply=1,
            human_input_mode="NEVER",
        )

def get_llm_config():
    """LLM konfigürasyonunu al"""
    import os
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment")
        return None
    
    return {
        "config_list": [{
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "api_key": api_key,
            "temperature": 0.3,
            "max_tokens": 4000
        }],
        "timeout": 300
}

def generate_proposal_from_analysis(
    folder_path: str,
    vendor_profile: Dict[str, Any],
    llm_config: Optional[Dict] = None
) -> str:
    """
    Analiz sonuçlarından teklif taslağı üret
    
    Args:
        folder_path: Fırsat klasörü yolu (opportunities/{code})
        vendor_profile: Şirket bilgileri ve past performance
        llm_config: LLM konfigürasyonu (opsiyonel)
    
    Returns:
        proposal.md dosyasının yolu
    """
    folder = Path(folder_path)
    
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    # 1) Analiz raporunu yükle
    report_path = folder / "report.json"
    if not report_path.exists():
        raise FileNotFoundError(f"report.json not found in {folder}")
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load report.json: {e}")
    
    # Report yapısını kontrol et (report.report veya direkt report)
    if 'report' in report:
        report_data = report['report']
    else:
        report_data = report
    
    # (Opsiyonel) Advisor summary varsa dahil et
    advisor_summary = None
    advisor_path = folder / "advisor_summary.json"
    if advisor_path.exists():
        try:
            with open(advisor_path, 'r', encoding='utf-8') as f:
                advisor_summary = json.load(f)
        except:
            pass
    
    # 2) LLM config
    if not llm_config:
        llm_config = get_llm_config()
        if not llm_config:
            raise ValueError("LLM configuration not available")
    
    # 3) Proposal ajanını oluştur
    agent = make_proposal_generator_agent(llm_config)
    if not agent:
        raise ValueError("Failed to create proposal generator agent")
    
    # 4) Girdi payload hazırla
    # F-string içinde backslash kullanılamaz, bu yüzden ayrı oluşturuyoruz
    advisor_section = ""
    if advisor_summary:
        advisor_section = f"[ADVISOR_SUMMARY]\n{json.dumps(advisor_summary, ensure_ascii=False, indent=2)}\n\n"
    
    prompt = f"""
Below is a federal opportunity analysis report and vendor profile. Use this information to create a professional proposal draft.

IMPORTANT: NEVER use or copy government contact information (name, email, phone, address) from the RFQ.

[OPPORTUNITY_REQUIREMENTS_REPORT]
{json.dumps(report_data, ensure_ascii=False, indent=2)}

[VENDOR_PROFILE]
{json.dumps(vendor_profile, ensure_ascii=False, indent=2)}

{advisor_section}Please use the template above to create a professional proposal draft. Return only the proposal text in Markdown format, no other explanations.
"""
    
    # 5) LLM çağrısı
    try:
        logger.info("[Proposal Generator] Generating proposal...")
        resp = agent.generate_reply(
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        proposal_md = resp.content if hasattr(resp, 'content') else str(resp)
        
        # Markdown code block'ları temizle
        if "```markdown" in proposal_md:
            proposal_md = proposal_md.split("```markdown")[1].split("```")[0].strip()
        elif "```" in proposal_md:
            proposal_md = proposal_md.split("```")[1].split("```")[0].strip()
        
        logger.info(f"[Proposal Generator] Proposal generated ({len(proposal_md)} chars)")
        
    except Exception as e:
        logger.error(f"[Proposal Generator] Error: {e}", exc_info=True)
        raise ValueError(f"Failed to generate proposal: {e}")
    
    # 6) Dosyaya yaz
    proposal_path = folder / "proposal.md"
    try:
        proposal_path.write_text(proposal_md, encoding='utf-8')
        logger.info(f"[Proposal Generator] Saved: {proposal_path}")
    except Exception as e:
        logger.error(f"[Proposal Generator] Failed to save: {e}")
        raise
    
    return str(proposal_path)


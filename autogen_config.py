"""
AutoGen Configuration for MergenAI Lite
Simplified configuration for LLM agents
"""

import os
from typing import Dict, Any

def get_llm_config() -> Dict[str, Any]:
    """LLM konfigürasyonu"""
    
    return {
        "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "temperature": 0.1,
        "max_tokens": 2000
    }

def get_agent_configs() -> Dict[str, Dict[str, Any]]:
    """AutoGen agent konfigürasyonları (basitleştirilmiş)"""
    
    return {
        "requirements_extractor": {
            "name": "RequirementsExtractor",
            "model": "gpt-3.5-turbo",
            "temperature": 0.1,
            "max_tokens": 2000,
            "system_message": """
            Sen bir ilan analiz uzmanısın. İlan dokümanlarından gereksinimleri çıkarırsın.
            Oda sayısı, AV gereksinimleri, tarih aralıkları ve kısıtları JSON formatında çıkar.
            """
        }
    }


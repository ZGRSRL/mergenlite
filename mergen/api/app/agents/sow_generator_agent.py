"""
Pass 3: SOWGeneratorAgent - Fallback SOW Markdown generation
Generates SOW Markdown from normalized JSON when template engine is unavailable.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    try:
        from autogen import AssistantAgent, UserProxyAgent
        AUTOGEN_AVAILABLE = True
    except ImportError:
        from pyautogen import AssistantAgent, UserProxyAgent
        AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False


class SOWGeneratorAgentUnavailableError(RuntimeError):
    pass


def create_sow_generator_agent(llm_model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> AssistantAgent:
    """Create SOWGeneratorAgent for Pass 3 (Fallback)."""
    if not AUTOGEN_AVAILABLE:
        raise SOWGeneratorAgentUnavailableError("pyautogen not installed")
    
    system_message = """You are a SOW Generator Agent (Pass 3 - Fallback).

Your task: Generate professional Statement of Work (SOW) in Markdown format from normalized RFQ data.

IMPORTANT RULES:
1. Follow federal SOW format (Appendix A - Event Summary, Appendix B - Requirements, etc.)
2. Create tables in Markdown format (use pipe tables)
3. Match Hotel SOW structure as closely as possible
4. DO NOT make up any data - if field is missing, clearly state "TBD" or "To Be Determined"
5. Include all sections:
   - Event Summary
   - Sleeping Room Requirements (with daily breakdown table)
   - Function Space Requirements (with daily breakdown table)
   - Meeting Room Setup table
   - Daily AV Requirements table
   - Food & Beverage Requirements (with daily breakdown table)
   - Commercial Terms
   - Compliance Requirements (FAR and EDAR clauses)
6. Use professional, clear language suitable for hotel management
7. Format dates consistently (YYYY-MM-DD or Month DD, YYYY)
8. Include capacity, setup types, and special requirements clearly

Output: Professional SOW in Markdown format only. No JSON, no explanations."""
    
    llm_config = {
        "config_list": [{
            "model": llm_model,
            "api_key": api_key,
        }],
        "temperature": 0.3,  # Slightly higher for creative formatting
    }
    
    return AssistantAgent(
        name="SOWGeneratorAgent",
        system_message=system_message,
        llm_config=llm_config,
        tools=[],
    )


def run_sow_generator_agent(
    normalized_json: Dict[str, Any],
    llm_model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
) -> str:
    """
    Run SOWGeneratorAgent (Pass 3) to generate SOW Markdown from normalized JSON.
    
    Args:
        normalized_json: Normalized JSON from Pass 2 ReviewerAgent
        llm_model: LLM model to use
        api_key: OpenAI API key (if None, uses environment variable)
        
    Returns:
        SOW text in Markdown format
    """
    if not AUTOGEN_AVAILABLE:
        raise SOWGeneratorAgentUnavailableError("pyautogen not installed")
    
    import os
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    
    if not api_key:
        logger.warning("No API key provided, SOWGeneratorAgent may not work")
    
    generator = create_sow_generator_agent(llm_model, api_key)
    user = UserProxyAgent(
        name="SOWGeneratorUser",
        code_execution_config=False,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=3,
    )
    
    generator_message = f"""Generate a professional Statement of Work (SOW) in Markdown format from the following normalized RFQ data.

Normalized RFQ Data:
{json.dumps(normalized_json, indent=2)}

REQUIREMENTS:
1. Follow federal SOW format with Appendices (Appendix A - Event Summary, Appendix B - Requirements, etc.)
2. Create all tables in Markdown pipe table format
3. Include:
   - Event Summary section
   - Sleeping Room Requirements table (daily breakdown)
   - Function Space Requirements table (daily breakdown)
   - Meeting Room Setup table
   - Daily AV Requirements table
   - Food & Beverage Requirements table (daily breakdown)
   - Commercial Terms section
   - Compliance Requirements section (FAR and EDAR clauses)
4. Use professional language suitable for hotel management
5. If any data is missing, clearly state "TBD" or "To Be Determined"
6. Format dates consistently
7. Include all capacity, setup, and special requirements

Output ONLY the SOW Markdown text. Do not include JSON, explanations, or code blocks."""
    
    try:
        user.initiate_chat(generator, message=generator_message)
        last_message = generator.last_message()
        
        if not last_message:
            raise RuntimeError("SOWGeneratorAgent produced no output")
        
        content = last_message.get("content", "")
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""
        if isinstance(content, dict):
            content = json.dumps(content)
        
        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = '\n'.join(lines)
        
        sow_markdown = content.strip()
        logger.info(f"SOWGeneratorAgent completed successfully ({len(sow_markdown)} chars)")
        return sow_markdown
        
    except Exception as exc:
        logger.error(f"Error in SOWGeneratorAgent: {exc}", exc_info=True)
        raise


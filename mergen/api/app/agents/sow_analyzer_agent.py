"""
AutoGen-based SOW analyzer agent that extracts detailed requirements from SOW documents.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)

try:
    try:
        from autogen import AssistantAgent, UserProxyAgent, tool
        AUTOGEN_AVAILABLE = True
    except ImportError:
        try:
            from pyautogen import AssistantAgent, UserProxyAgent
            AUTOGEN_AVAILABLE = True
        except ImportError:
            from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
            # tool decorator not available in new API, will be handled differently
            tool = None  # Will be handled at usage point
            AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False


class SOWAnalyzerUnavailableError(RuntimeError):
    pass


def create_sow_analyzer_agent(llm_model: str = "gpt-4o-mini") -> AssistantAgent:
    """Create an AutoGen agent for analyzing SOW documents."""
    if not AUTOGEN_AVAILABLE:
        raise SOWAnalyzerUnavailableError("pyautogen not installed. Run `pip install pyautogen`.")

    import os
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    
    if not api_key:
        logger.warning("OPENAI_API_KEY or AZURE_OPENAI_API_KEY not set. AutoGen may not work without API key.")
        # Try to use default OpenAI config (may work if key is set elsewhere)
        llm_config = {
            "config_list": [
                {
                    "model": llm_model,
                }
            ],
            "temperature": 0.1,
        }
    else:
        llm_config = {
            "config_list": [
                {
                    "model": llm_model,
                    "api_key": api_key,
                }
            ],
            "temperature": 0.1,  # Low temperature for accurate extraction
        }

    system_message = """You are a SOW (Statement of Work) Analyzer Agent. Your task is to extract detailed, structured information from SOW documents.

Extract ALL the following information from the provided SOW document:

1. **Event Details:**
   - Event name
   - Solicitation number
   - Agency
   - Dates (start, end, duration)
   - Location (city, state, country)
   - Submission due date

2. **Sleeping Room Requirements:**
   - Daily breakdown (day, date, number of rooms per night)
   - Total room nights
   - Any special room requirements

3. **Function Space Requirements:**
   - Daily breakdown (day, date)
   - Room types needed (Registration, General Session, Breakouts, Logistics, etc.)
   - Capacity requirements
   - Setup requirements

4. **AV (Audio/Visual) Requirements:**
   - Room-by-room AV needs
   - Setup requirements (Hollow Square, Theater, Classroom, etc.)
   - Capacity for each room
   - Special notes (power strips, audio feeds, etc.)
   - 24-hour hold requirements
   - Hybrid meeting requirements (OWLs, Zoom management, etc.)
   - Court reporter audio feed requirements
   - Breakout room power & setup needs

5. **Food & Beverage Requirements:**
   - Daily breakdown (day, date, time, headcount, menu)
   - Appetizers, beverages, coffee, lunch, box lunches, etc.

6. **Commercial Terms:**
   - NAICS Code
   - PSC Code
   - Set-Aside type
   - Size standard
   - ADA compliance requirements
   - Wi-Fi/Internet requirements
   - Parking requirements
   - Cancellation terms
   - AV discount requirements
   - F&B discount requirements

7. **Cost Proposal & Budget:**
   - Quote due date
   - Submission method
   - Submission email
   - Required attachments

8. **Evaluation and Award Criteria:**
   - Payment terms
   - Tax exemption status
   - Billing method
   - Cancellation policy

9. **Compliance Requirements:**
   - FAR clauses (list all clause numbers and titles)
   - EDAR clauses (list all clause numbers and titles)

10. **Appendices:**
    - Any additional documents or requirements

Respond with a comprehensive JSON structure containing ALL extracted information. Be thorough and extract every detail mentioned in the document."""

    assistant = AssistantAgent(
        name="SOWAnalyzerAgent",
        system_message=system_message,
        llm_config=llm_config,
        tools=[],
    )
    return assistant


def analyze_sow_document(
    document_text: str,
    llm_model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze a SOW document using AutoGen agent to extract detailed requirements.
    
    Args:
        document_text: Full text content of the SOW document
        llm_model: LLM model to use for analysis
        api_key: OpenAI API key (if None, uses environment variable)
        
    Returns:
        Dict containing extracted SOW requirements
    """
    if not AUTOGEN_AVAILABLE:
        raise SOWAnalyzerUnavailableError("pyautogen not installed. Run `pip install pyautogen`.")

    import os
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")

    assistant = create_sow_analyzer_agent(llm_model=llm_model, api_key=api_key)
    # New autogen_agentchat API uses different parameters
    try:
        user = UserProxyAgent(
            name="SOWAnalysisUser",
            code_execution_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
        )
    except TypeError:
        # New API (autogen_agentchat) - simplified parameters
        user = UserProxyAgent(name="SOWAnalysisUser")
    
    user_message = f"""Please analyze the following SOW document and extract ALL requirements in detail.

Document Text:
{document_text}

Extract all information and respond with a comprehensive JSON structure containing:
- Event details
- Sleeping room requirements (daily breakdown)
- Function space requirements (daily breakdown)
- AV requirements (room-by-room with all details)
- Food & beverage requirements (daily breakdown)
- Commercial terms
- Cost proposal requirements
- Evaluation criteria
- Compliance requirements (all FAR and EDAR clauses)
- Appendices

Respond ONLY with valid JSON. Do not include any explanatory text outside the JSON structure."""

    try:
        user.initiate_chat(assistant, message=user_message)
        last_message = assistant.last_message()
        
        if not last_message:
            raise RuntimeError("SOW analyzer produced no output.")
        
        content = last_message.get("content", "")
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""
        if isinstance(content, dict):
            return content
        
        # Try to extract JSON from response
        # Sometimes LLM wraps JSON in markdown code blocks
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        
        # Try to find JSON object in response
        if "{" in content and "}" in content:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            content = content[json_start:json_end]
        
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse SOW analyzer JSON output: {e}")
        logger.error(f"Raw content: {content[:500]}")
        # Return a structured error response
        return {
            "error": "Failed to parse LLM response as JSON",
            "raw_content_preview": content[:500] if content else "",
            "extraction_error": str(e),
        }
    except Exception as exc:
        logger.error(f"Error in SOW analysis: {exc}", exc_info=True)
        raise


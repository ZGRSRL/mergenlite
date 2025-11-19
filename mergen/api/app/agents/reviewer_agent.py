"""
Pass 2: ReviewerAgent - Error correction and normalization
Reviews raw analyzer JSON output and corrects errors, normalizes data.
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
        try:
            from pyautogen import AssistantAgent, UserProxyAgent
            AUTOGEN_AVAILABLE = True
        except ImportError:
            from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
            AUTOGEN_AVAILABLE = True
except ImportError:
    AUTOGEN_AVAILABLE = False


class ReviewerAgentUnavailableError(RuntimeError):
    pass


def create_reviewer_agent(llm_model: str = "gpt-4o-mini", api_key: Optional[str] = None) -> AssistantAgent:
    """Create ReviewerAgent for Pass 2."""
    if not AUTOGEN_AVAILABLE:
        raise ReviewerAgentUnavailableError("pyautogen not installed")
    
    system_message = """You are a Requirements Reviewer Agent (Pass 2).

Your task: Review and correct the raw analyzer JSON output from Pass 1.

CORRECT:
- Contradictory information (e.g., dates don't match, room counts inconsistent)
- Missing values (fill with reasonable inference OR mark as "TBD" if uncertain)
- Date format normalization (use YYYY-MM-DD format)
- Room number totals (sum up daily breakdowns, verify totals)
- Table OCR errors (fix misread numbers, text)
- Merge duplicate lists (remove duplicates, consolidate)
- Ensure 100% schema compliance with SOWDataModel

CRITICAL RULES:
1. DO NOT make up data - if uncertain, use "TBD"
2. Preserve all valid data from Pass 1
3. Normalize date formats consistently
4. Verify numerical totals (rooms, capacity, headcount)
5. Fix obvious OCR/parsing errors
6. Output must be valid JSON matching SOWDataModel schema

Output: Clean normalized JSON that strictly follows SOWDataModel schema."""
    
    llm_config = {
        "config_list": [{
            "model": llm_model,
            "api_key": api_key,
        }],
        "temperature": 0.1,  # Low temperature for accuracy
    }
    
    return AssistantAgent(
        name="ReviewerAgent",
        system_message=system_message,
        llm_config=llm_config,
        tools=[],
    )


def run_reviewer_agent(
    raw_analyzer_json: Dict[str, Any],
    llm_model: str = "gpt-4o-mini",
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run ReviewerAgent (Pass 2) to correct errors and normalize analyzer JSON.
    
    Args:
        raw_analyzer_json: Raw JSON output from Pass 1 AnalyzerAgent
        llm_model: LLM model to use
        api_key: OpenAI API key (if None, uses environment variable)
        
    Returns:
        Normalized JSON dict following SOWDataModel schema
    """
    if not AUTOGEN_AVAILABLE:
        raise ReviewerAgentUnavailableError("pyautogen not installed")
    
    import os
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    
    if not api_key:
        logger.warning("No API key provided, ReviewerAgent may not work")
    
    reviewer = create_reviewer_agent(llm_model, api_key)
    # New autogen_agentchat API uses different parameters
    try:
        user = UserProxyAgent(
            name="ReviewerUser",
            code_execution_config=False,
            human_input_mode="NEVER",
            max_consecutive_auto_reply=3,
        )
    except TypeError:
        # New API (autogen_agentchat) - simplified parameters
        user = UserProxyAgent(name="ReviewerUser")
    
    reviewer_message = f"""Review and correct the following raw analyzer JSON output.

Raw Analyzer Output (Pass 1):
{json.dumps(raw_analyzer_json, indent=2)}

CORRECT:
- Contradictory information (dates, room counts, capacities)
- Missing values (fill or mark as "TBD")
- Date format normalization (use YYYY-MM-DD)
- Room number totals (verify and fix)
- Table OCR errors
- Merge duplicate lists
- Ensure 100% schema compliance

Output ONLY valid normalized JSON that strictly follows SOWDataModel schema. Do not include any explanatory text."""
    
    try:
        user.initiate_chat(reviewer, message=reviewer_message)
        last_message = reviewer.last_message()
        
        if not last_message:
            raise RuntimeError("ReviewerAgent produced no output")
        
        content = last_message.get("content", "")
        if isinstance(content, list):
            content = content[0].get("text", "") if content else ""
        if isinstance(content, dict):
            return content
        
        # Extract JSON from response
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        
        if "{" in content and "}" in content:
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            content = content[json_start:json_end]
        
        normalized_json = json.loads(content)
        logger.info("ReviewerAgent completed successfully")
        return normalized_json
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse ReviewerAgent JSON output: {e}")
        logger.error(f"Raw content: {content[:500]}")
        # Return original with error marker
        return {
            **raw_analyzer_json,
            "_reviewer_error": str(e),
            "_raw_content_preview": content[:500] if content else "",
        }
    except Exception as exc:
        logger.error(f"Error in ReviewerAgent: {exc}", exc_info=True)
        raise


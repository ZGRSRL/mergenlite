"""
AutoGen-based hotel matcher agent that queries Amadeus and returns scored hotels.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from ..services.amadeus_client import search_hotels_by_city_code

logger = logging.getLogger(__name__)

try:
    # pyautogen 0.10.0+ uses different import structure
    try:
        from autogen import AssistantAgent, UserProxyAgent, tool
        AUTOGEN_AVAILABLE = True
    except ImportError:
        # Try new pyautogen structure
        from pyautogen import AssistantAgent, UserProxyAgent
        from pyautogen.agentchat.contrib.capabilities.teachable_agent import TeachableAgent
        # For tool decorator, use function annotation instead
        AUTOGEN_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    AUTOGEN_AVAILABLE = False


class HotelMatcherUnavailableError(RuntimeError):
    pass


if AUTOGEN_AVAILABLE:

    @tool
    def amadeus_search_hotels_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        """Call Amadeus hotel search and return raw offers."""
        city_code = params["city_code"]
        check_in = params["check_in"]
        check_out = params["check_out"]
        adults = int(params.get("adults", 1))
        max_results = int(params.get("max_results", 5))
        offers = search_hotels_by_city_code(city_code, check_in, check_out, adults, max_results)
        return {"offers": offers}


def create_hotel_matcher_agent(llm_model: str = "gpt-4o-mini") -> AssistantAgent:
    if not AUTOGEN_AVAILABLE:
        raise HotelMatcherUnavailableError("pyautogen not installed. Run `pip install pyautogen`.")

    import os
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    
    if not api_key:
        logger.warning("OPENAI_API_KEY or AZURE_OPENAI_API_KEY not set. AutoGen may not work without API key.")
        llm_config = {
            "config_list": [
                {
                    "model": llm_model,
                }
            ],
            "temperature": 0.2,
        }
    else:
        llm_config = {
            "config_list": [
                {
                    "model": llm_model,
                    "api_key": api_key,
                }
            ],
            "temperature": 0.2,
        }

    system_message = (
        "You are HotelMatcherAgent. "
        "Given RFQ requirements (city_code, dates, attendees) and optional historical hints, call `amadeus_search_hotels_tool` "
        "to retrieve offers and respond with JSON: "
        '{"hotels": [{"name": "...","amadeus_hotel_id": "...","score":0.9,"currency":"USD","total_price":1234.5,'
        '"notes":"..."}], "reasoning": "..."}'
    )
    assistant = AssistantAgent(
        name="HotelMatcherAgent",
        system_message=system_message,
        llm_config=llm_config,
        tools=[amadeus_search_hotels_tool] if AUTOGEN_AVAILABLE else [],
    )
    return assistant


def run_hotel_match_for_opportunity(
    requirements: Dict[str, Any],
    decision_hint: Optional[Dict[str, Any]] = None,
    llm_model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    if not AUTOGEN_AVAILABLE:
        raise HotelMatcherUnavailableError("pyautogen not installed. Run `pip install pyautogen`.")

    assistant = create_hotel_matcher_agent(llm_model=llm_model)
    user = UserProxyAgent(
        name="HotelMatchUser",
        code_execution_config=False,
        human_input_mode="NEVER",
    )
    user_message = (
        "Here are the hotel search requirements:\n"
        f"{json.dumps(requirements, indent=2)}\n\n"
    )
    if decision_hint:
        hint_lines = [
            "Historical decision cache context:",
            json.dumps({k: v for k, v in decision_hint.items() if k != 'cached_hotels'}, indent=2),
        ]
        cached_hotels = decision_hint.get("cached_hotels")
        if cached_hotels:
            hint_lines.append("Previously recommended hotels:")
            hint_lines.append(json.dumps(cached_hotels, indent=2))
        user_message += "\n".join(hint_lines) + "\n\n"

    user_message += "Use the Amadeus tool to fetch hotels and respond strictly with JSON as described."
    user.initiate_chat(assistant, message=user_message)
    last_message = assistant.last_message()
    if not last_message:
        raise RuntimeError("Hotel matcher produced no output.")
    content = last_message.get("content")
    if isinstance(content, list):
        content = content[0].get("text") if content else ""
    if isinstance(content, dict):
        return content
    try:
        return json.loads(content)
    except Exception as exc:
        logger.error("Failed to parse hotel matcher output: %s", exc)
        raise

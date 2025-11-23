"""
AutoGen-based hotel matcher agent that queries Amadeus and returns scored hotels.
DEBUG VERSION: WRITES TO /tmp/hotel_debug.log
"""
from __future__ import annotations

import json
import logging
import time
import re
import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional, List

from ..services.amadeus_client import search_hotels_by_city_code
from ..config import settings

logger = logging.getLogger(__name__)

# --- DEBUG HELPER ---
def debug_log(message):
    """Writes debug messages directly to a file to bypass stdout buffering issues."""
    try:
        import os
        # Ensure directory exists
        log_dir = "/tmp"
        os.makedirs(log_dir, exist_ok=True)
        
        log_path = "/tmp/hotel_debug.log"
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
            f.flush()  # Force write to disk
        # Also print to stderr for immediate visibility
        import sys
        print(f"[DEBUG] {message}", file=sys.stderr, flush=True)
    except Exception as e:
        # Try to log the error itself
        try:
            import sys
            print(f"[DEBUG ERROR] Failed to write log: {e}", file=sys.stderr, flush=True)
        except:
            pass
# --------------------

# Import LLM logger for database logging
try:
    # Try logging_service first (if renamed), fallback to llm_logger
    try:
        from ..services.logging_service import log_llm_call
    except ImportError:
        from ..services.llm_logger import log_llm_call
    from ..db import SessionLocal
    LLM_LOGGER_AVAILABLE = True
except ImportError:
    LLM_LOGGER_AVAILABLE = False
    logger.warning("LLM logger not available - LLM calls will not be logged to database")

# Use autogen package (standard, supports llm_config)
# Priority: autogen (0.10.x) > autogen_agentchat (new API)
try:
    from autogen import AssistantAgent, UserProxyAgent
    try:
        from autogen import tool
    except ImportError:
        tool = None  # tool decorator may not be available in all versions
    AUTOGEN_AVAILABLE = True
    AUTOGEN_NEW_API = False
    logger.info("Using autogen package (standard API with llm_config)")
except ImportError:
    # Fallback to autogen_agentchat only if autogen is not available
    try:
        from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
        tool = None  # tool decorator not available in new API
        AUTOGEN_AVAILABLE = True
        AUTOGEN_NEW_API = True
        logger.info("Using autogen_agentchat package (new API)")
    except ImportError:
        AUTOGEN_AVAILABLE = False
        AUTOGEN_NEW_API = False
        logger.warning("Neither autogen nor autogen_agentchat available")


class HotelMatcherUnavailableError(RuntimeError):
    pass


def _convert_amadeus_offers_to_hotels(
    offers: List[Dict[str, Any]],
    city_code: str,
    check_in: str,
    check_out: str,
) -> List[Dict[str, Any]]:
    """Convert Amadeus API offers to hotel match format."""
    hotels: List[Dict[str, Any]] = []
    logger.info(f"[convert] Converting {len(offers)} offers from Amadeus")

    def find_name_recursive(obj: Any, depth: int = 0, max_depth: int = 4) -> Optional[str]:
        if depth > max_depth:
            return None
        if isinstance(obj, dict):
            for key in ("name", "hotelName", "propertyName"):
                val = obj.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip()
            for val in obj.values():
                if isinstance(val, (dict, list)):
                    result = find_name_recursive(val, depth + 1, max_depth)
                    if result:
                        return result
        elif isinstance(obj, list):
            for item in obj:
                result = find_name_recursive(item, depth + 1, max_depth)
                if result:
                    return result
        return None

    from datetime import datetime

    for offer_data in offers:
        hotel_name = offer_data.get("name")
        if not hotel_name:
            hotel_name = offer_data.get("hotel", {}).get("name")
        if not hotel_name:
            hotel_name = find_name_recursive(offer_data)
        if not hotel_name:
            hotel_name = "Unknown Hotel"
            logger.warning(f"[convert] Could not determine hotel name; keys={list(offer_data.keys())}")

        total_price = 0.0
        price_data = offer_data.get("price") or offer_data.get("offer", {}).get("price")
        if isinstance(price_data, dict):
            try:
                total_price = float(price_data.get("total", 0))
            except (TypeError, ValueError):
                total_price = 0.0

        avg_price = 0.0
        if total_price > 0:
            try:
                nights = (datetime.fromisoformat(check_out) - datetime.fromisoformat(check_in)).days
                if nights > 0:
                    avg_price = total_price / nights
            except Exception:
                avg_price = 0.0

        hotel = {
            "name": hotel_name,
            "amadeus_hotel_id": offer_data.get("hotelId") or offer_data.get("hotel", {}).get("hotelId"),
            "city": offer_data.get("cityCode", city_code),
            "price_per_night": round(avg_price, 2) if avg_price else 0,
            "total_price": round(total_price, 2) if total_price else 0,
            "distance": offer_data.get("distance", "Unknown"),
            "score": 0.7,
            "reasoning": "Generated via direct Amadeus API call",
            "offer": offer_data,
        }
        hotels.append(hotel)

    return hotels


def _execute_manual_fallback(requirements: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Executes the search manually without any LLM involvement."""
    debug_log(f"FALLBACK: Executing manual search. Reason: {reason}")
    
    try:
        city_code = requirements.get("city_code")
        check_in = requirements.get("check_in")
        check_out = requirements.get("check_out")
        adults = requirements.get("adults", 1)

        if not city_code or not check_in or not check_out:
            msg = "Missing required parameters (city_code, check_in, check_out)"
            debug_log(f"FALLBACK ERROR: {msg}")
            return {
                "error": msg,
                "hotels": [],
                "reasoning": msg,
                "requirements_analysis": {
                    "lodging_requirements_met": False,
                    "transportation_requirements_met": False,
                    "amenities_requirements_met": False,
                    "summary": msg,
                },
            }

        debug_log(f"FALLBACK: Calling Amadeus API directly - city={city_code}, check_in={check_in}, check_out={check_out}, adults={adults}")
        
        # Try with requested adults first
        offers = search_hotels_by_city_code(city_code, check_in, check_out, adults, max_results=10)
        
        # Fallback to adults=1 if no results
        if not offers and adults > 1:
            debug_log(f"FALLBACK: No offers for {adults} adults, retrying with adults=1")
            offers = search_hotels_by_city_code(city_code, check_in, check_out, 1, max_results=10)
        
        if not offers:
            msg = "Amadeus API returned no hotels"
            debug_log(f"FALLBACK: {msg}")
            return {
                "error": msg,
                "hotels": [],
                "reasoning": f"Automatic fallback triggered. Reason: {reason}. {msg}",
                "requirements_analysis": {
                    "lodging_requirements_met": False,
                    "transportation_requirements_met": False,
                    "amenities_requirements_met": False,
                    "summary": msg,
                },
            }

        debug_log(f"FALLBACK SUCCESS: Found {len(offers)} offers")
        hotels = _convert_amadeus_offers_to_hotels(offers, city_code, check_in, check_out)
        reasoning = f"Automatic fallback triggered. Reason: {reason}. Found {len(hotels)} hotels via direct Amadeus API."
        
        return {
            "hotels": hotels,
            "reasoning": reasoning,
            "requirements_analysis": {
                "lodging_requirements_met": False,
                "transportation_requirements_met": False,
                "amenities_requirements_met": False,
                "summary": reasoning,
            },
            "fallback_used": True,
        }
    except Exception as e:
        debug_log(f"FALLBACK FAILED: {e}")
        import traceback
        debug_log(f"FALLBACK TRACEBACK: {traceback.format_exc()}")
        return {
            "error": str(e),
            "hotels": [],
            "reasoning": f"Fallback execution failed: {str(e)}",
            "requirements_analysis": {
                "lodging_requirements_met": False,
                "transportation_requirements_met": False,
                "amenities_requirements_met": False,
                "summary": f"Fallback failed: {str(e)}",
            },
        }


def _direct_hotel_match_response(
    requirements: Dict[str, Any],
    failure_reason: Optional[str] = None,
) -> Dict[str, Any]:
    """Use Amadeus API directly without AutoGen."""
    city_code = requirements.get("city_code")
    check_in = requirements.get("check_in")
    check_out = requirements.get("check_out")
    adults = requirements.get("adults", 2)

    if not city_code or not check_in or not check_out:
        msg = "Missing required parameters (city_code, check_in, check_out)"
        logger.warning(f"[direct] {msg}")
        return {
            "error": msg,
            "hotels": [],
            "reasoning": msg,
            "requirements_analysis": {
                "lodging_requirements_met": False,
                "transportation_requirements_met": False,
                "amenities_requirements_met": False,
                "summary": msg,
            },
        }

    logger.info(
        f"[direct] Calling Amadeus API directly (city={city_code}, check_in={check_in}, "
        f"check_out={check_out}, adults={adults})"
    )
    offers = search_hotels_by_city_code(city_code, check_in, check_out, adults, max_results=10)
    if not offers:
        msg = "Amadeus API returned no hotels"
        logger.warning(f"[direct] {msg}")
        return {
            "error": msg,
            "hotels": [],
            "reasoning": msg,
            "requirements_analysis": {
                "lodging_requirements_met": False,
                "transportation_requirements_met": False,
                "amenities_requirements_met": False,
                "summary": msg,
            },
            "fallback_used": True,
        }

    hotels = _convert_amadeus_offers_to_hotels(offers, city_code, check_in, check_out)
    reasoning = failure_reason or f"Direct Amadeus API call returned {len(hotels)} hotels."
    return {
        "hotels": hotels,
        "reasoning": reasoning,
        "requirements_analysis": {
            "lodging_requirements_met": False,
            "transportation_requirements_met": False,
            "amenities_requirements_met": False,
            "summary": reasoning,
        },
        "fallback_used": bool(failure_reason),
    }


if AUTOGEN_AVAILABLE:
    # Tool decorator - use if available, otherwise define function normally
    def amadeus_search_hotels_tool(params: Dict[str, Any]) -> Dict[str, Any]:
        """Call Amadeus hotel search with AUTO-RETRY logic for high occupancy.
        
        Args:
            params: Dictionary with keys:
                - city_code: IATA city code (e.g., "PHL")
                - check_in: Check-in date (YYYY-MM-DD)
                - check_out: Check-out date (YYYY-MM-DD)
                - adults: Number of adults (default: 1)
                - max_results: Maximum number of results (default: 5)
        
        Returns:
            Dictionary with "offers" key containing list of hotel offers, or {"error": "message"} if search fails.
            
        Strategy:
            - First attempt: Use requested adults count
            - Fallback: If first attempt fails and adults > 1, retry with adults=1
            - This handles "NO RATE FOR REQUESTED OCCUPANCY" errors gracefully
        """
        try:
            city_code = params.get("city_code")
            check_in = params.get("check_in")
            check_out = params.get("check_out")
            try:
                original_adults = int(params.get("adults", 1))
            except (ValueError, TypeError):
                original_adults = 1
            max_results = int(params.get("max_results", 5))
            
            if not city_code or not check_in or not check_out:
                return {
                    "error": "Missing required parameters: city_code, check_in, and check_out are required",
                    "offers": []
                }
            
            logger.info(f"🏨 Search Attempt 1: city={city_code}, check_in={check_in}, check_out={check_out}, adults={original_adults}")
            
            # 1. FIRST ATTEMPT with requested adults
            offers = search_hotels_by_city_code(city_code, check_in, check_out, original_adults, max_results)
            
            if offers:
                logger.info(f"✅ Amadeus tool returned {len(offers)} offers on first attempt")
                return {"offers": offers}
            
            # 2. FALLBACK: If first attempt returned no offers and adults > 1, retry with adults=1
            if original_adults > 1:
                logger.info(f"🔄 Fallback triggered: Retrying with adults=1 for {city_code} (original request was {original_adults} adults)")
                fallback_offers = search_hotels_by_city_code(city_code, check_in, check_out, 1, max_results)
                
                if fallback_offers:
                    logger.info(f"✅ Fallback successful: Found {len(fallback_offers)} offers with adults=1")
                    return {
                        "offers": fallback_offers,
                        "warning": f"Original search for {original_adults} adults returned no results. Showing rates for 1 adult per room. Please note: These rates may not reflect the actual cost for {original_adults} adults."
                    }
            
            # No offers found even after fallback
            logger.warning(f"❌ No offers found from Amadeus API for {city_code} on {check_in} to {check_out} (even after fallback)")
            return {
                "offers": [],
                "error": f"No hotel offers found for {city_code} on dates {check_in} to {check_out}. This may be due to: 1) No availability for these dates, 2) Dates too far in the future (2026), 3) Amadeus test environment limitations, 4) High occupancy requirements not available."
            }
        except Exception as e:
            logger.error(f"Amadeus tool error: {e}", exc_info=True)
            return {
                "error": f"Amadeus API error: {str(e)}",
                "offers": []
            }
    
    # Apply tool decorator if available
    if tool is not None:
        amadeus_search_hotels_tool = tool(amadeus_search_hotels_tool)
        logger.info("Amadeus tool decorated and ready")
    else:
        logger.warning("Tool decorator not available - tool may not work with AutoGen")


def create_hotel_matcher_agent(llm_model: str = "gpt-4o-mini") -> AssistantAgent:
    debug_log(f"create_hotel_matcher_agent called with model: {llm_model}")
    if not AUTOGEN_AVAILABLE:
        raise HotelMatcherUnavailableError("pyautogen not installed. Run `pip install pyautogen`.")

    import os
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    debug_log(f"API key found: {bool(api_key)}")
    
    system_message = """You are HotelMatcherAgent, an expert hotel matching agent that analyzes hotels from Amadeus API against detailed SOW (Statement of Work) requirements.

**YOUR TASK:**
1. Call `amadeus_search_hotels_tool` with the provided city_code, check_in, check_out, and adults parameters
2. **CRITICAL:** If the tool returns offers, you MUST process them and return a JSON response with the 'hotels' array containing all analyzed hotels
3. **CRITICAL:** If the tool returns NO offers or an error, you MUST still return valid JSON with an empty 'hotels' array and a 'reasoning' field explaining why
4. Analyze each hotel offer against the SOW requirements provided
5. Score hotels based on how well they match the requirements
6. Return a ranked list of hotels with detailed analysis

**ABSOLUTE REQUIREMENT:**
- You MUST ALWAYS return valid JSON, never an empty message or plain text
- Your response MUST start with '{' and end with '}'
- If no hotels are found, return: {"hotels": [], "reasoning": "Explanation here", "requirements_analysis": {...}}
- If hotels are found, return: {"hotels": [...], "reasoning": "Analysis here", "requirements_analysis": {...}}

**SOW REQUIREMENTS TO ANALYZE:**

1. **Lodging Requirements:**
   - Room count per city (min/max): Check if hotel can accommodate the required room block
   - Cancellation policy: Verify if hotel offers:
     * Free cancellation 48+ hours before check-in
     * Force majeure (no penalty) provisions
     * Name change/guest change allowed until check-in
   - Uniform terms: Check if hotel offers consistent pricing/conditions (if required)
   - Required amenities: Verify hotel has:
     * Loyalty program benefits
     * Complimentary parking
     * Free Wi-Fi
     * Any other specified amenities

2. **Transportation Requirements:**
   - Maximum distance: Check if hotel is within the specified radius (e.g., 3 miles) from venue/stadium
   - Transportation options: Note available options (rideshare, shuttle, public transit, walking distance)
   - If distance is not provided in hotel data, estimate based on city center or use "Unknown" but note it

3. **Location Requirements:**
   - If multiple cities are specified, analyze hotels for each city separately
   - Match hotel location to specified ZIP codes if provided
   - Consider proximity to stadium/venue if specified

4. **Period of Performance:**
   - Verify hotel availability matches the required date range
   - Check if hotel can accommodate extended stays (if max_stay_days specified)

5. **Price Analysis:**
   - Compare total price (including taxes) across hotels
   - Note if pricing is competitive for the required room block
   - Consider value proposition (amenities vs. price)

**SCORING CRITERIA (0.0 to 1.0):**
- **0.9-1.0 (Excellent):** Meets all critical requirements (cancellation policy, amenities, distance, availability)
- **0.7-0.8 (Good):** Meets most requirements, minor gaps acceptable
- **0.5-0.6 (Fair):** Meets basic requirements but missing some important features
- **0.0-0.4 (Poor):** Does not meet critical requirements

**OUTPUT FORMAT:**
Respond with JSON containing:
{
  "hotels": [
    {
      "name": "Hotel Name",
      "amadeus_hotel_id": "hotel_id_from_amadeus",
      "score": 0.85,
      "currency": "USD",
      "total_price": 1234.5,
      "price_per_night": 246.9,
      "distance_miles": 2.5,
      "distance_to_venue": "2.5 miles from venue",
      "cancellation_policy_match": true,
      "amenities_match": true,
      "amenities_found": ["free_wifi", "parking", "loyalty_program"],
      "amenities_missing": [],
      "room_availability": "Available for required dates",
      "transportation_options": ["rideshare", "shuttle", "public_transit"],
      "notes": "Detailed analysis of why this hotel matches or doesn't match requirements",
      "compliance_score": {
        "lodging_requirements": 0.9,
        "transportation": 0.8,
        "amenities": 1.0,
        "price": 0.7
      }
    }
  ],
  "reasoning": "Overall analysis of hotel search results and how they match SOW requirements",
  "requirements_analysis": {
    "lodging_requirements_met": true,
    "transportation_requirements_met": true,
    "amenities_requirements_met": true,
    "summary": "X out of Y hotels meet all critical requirements"
  }
}

**IMPORTANT:**
- Always analyze hotels against ALL provided SOW requirements
- If a requirement cannot be verified from Amadeus data, note it in the "notes" field
- Prioritize hotels that meet cancellation policy and amenity requirements
- Consider distance/transportation as a key factor in scoring
- Provide detailed reasoning for each hotel's score

**CRITICAL - OUTPUT FORMAT:**
- You MUST respond with valid JSON only, never plain text
- If you cannot search for hotels (e.g., missing city_code, API error), return JSON with an "error" field:
  {
    "error": "Description of the problem",
    "hotels": [],
    "reasoning": "Why the search could not be performed"
  }
- Never return plain text error messages - always use JSON format"""
    
    # Try old API first (more stable), then fall back to new API if needed
    # Old API - use llm_config
    if not api_key:
        logger.warning("OPENAI_API_KEY or AZURE_OPENAI_API_KEY not set. AutoGen may not work without API key.")
        # ADDING TIMEOUT TO CONFIG
        llm_config = {
            "config_list": [
                {
                    "model": llm_model,
                }
            ],
            "temperature": 0.2,
            "timeout": 45,  # Request timeout
            "request_timeout": 45
        }
    else:
        # ADDING TIMEOUT TO CONFIG
        llm_config = {
            "config_list": [
                {
                    "model": llm_model,
                    "api_key": api_key,
                }
            ],
            "temperature": 0.2,
            "timeout": 45,  # Request timeout
            "request_timeout": 45
        }

    # Use llm_config with autogen (standard API)
    # autogen 0.10.x supports llm_config, not direct model parameter
    debug_log("Creating AssistantAgent...")
    try:
        # First try with tools if available
        if AUTOGEN_AVAILABLE and tool is not None:
            try:
                debug_log("Attempting to create AssistantAgent with tools...")
                assistant = AssistantAgent(
                    name="HotelMatcherAgent",
                    system_message=system_message,
                    llm_config=llm_config,
                    tools=[amadeus_search_hotels_tool],
                )
                debug_log("AssistantAgent created with tools successfully")
                logger.info("HotelMatcherAgent created with tools")
            except TypeError:
                # Tools not supported, try without
                debug_log("Tools not supported, retrying without tools...")
                logger.warning("AssistantAgent rejected tools parameter; retrying without tools")
                assistant = AssistantAgent(
                    name="HotelMatcherAgent",
                    system_message=system_message,
                    llm_config=llm_config,
                )
                debug_log("AssistantAgent created without tools successfully")
                logger.info("HotelMatcherAgent created without tools")
        else:
            # No tools available, create without
            debug_log("No tools available, creating AssistantAgent without tools...")
            assistant = AssistantAgent(
                name="HotelMatcherAgent",
                system_message=system_message,
                llm_config=llm_config,
            )
            debug_log("AssistantAgent created (no tools) successfully")
            logger.info("HotelMatcherAgent created (no tools available)")
    except TypeError as exc:
        # If llm_config is also rejected, this is a version mismatch
        error_msg = str(exc)
        logger.error(f"AssistantAgent initialization failed: {error_msg}")
        if "model" in error_msg.lower():
            raise HotelMatcherUnavailableError(
                f"AutoGen version mismatch: AssistantAgent does not accept llm_config. "
                f"Error: {error_msg}. Please ensure autogen>=0.10.0 is installed."
            ) from exc
        else:
            raise HotelMatcherUnavailableError(
                f"AutoGen AssistantAgent initialization failed: {error_msg}"
            ) from exc
    
    return assistant


def run_hotel_match_for_opportunity(
    requirements: Dict[str, Any],
    decision_hint: Optional[Dict[str, Any]] = None,
    sow_requirements: Optional[Dict[str, Any]] = None,
    llm_model: str = "gpt-4o-mini",
    agent_run_id: Optional[int] = None,
) -> Dict[str, Any]:
    # CRITICAL: Log function entry immediately
    debug_log("\n" + "="*70)
    debug_log(f"FUNCTION ENTRY: run_hotel_match_for_opportunity")
    debug_log(f"Requirements: {requirements}")
    debug_log("="*70)
    """
    Run hotel matching with SOW requirements analysis.
    
    Args:
        requirements: Basic hotel search requirements (city_code, check_in, check_out, adults)
        decision_hint: Optional decision cache hint
        sow_requirements: SOW analysis requirements (LodgingRequirements, TransportationRequirements, etc.)
        llm_model: LLM model to use
    """
    if not AUTOGEN_AVAILABLE:
        debug_log("ERROR: AutoGen library missing. Switching to manual fallback.")
        return _execute_manual_fallback(requirements, "AutoGen Library Missing")
    
    # Check API key
    import os
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    if not api_key:
        debug_log("ERROR: API Key missing. Switching to manual fallback.")
        return _execute_manual_fallback(requirements, "LLM API Key Missing")
    
    # GLOBAL TIMEOUT PROTECTION: Wrap ENTIRE agent lifecycle
    # This includes agent creation, which was hanging
    TIMEOUT_SECONDS = 45
    
    class GlobalTimeoutError(Exception):
        pass
    
    def timeout_handler(signum, frame):
        raise GlobalTimeoutError("Operation timed out (Global Safe-Guard)")
    
    # Set up signal timeout (only works in main thread, but we try anyway)
    signal_obj = None
    try:
        import signal
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(TIMEOUT_SECONDS)
        signal_obj = signal
        debug_log(f"Global timeout set ({TIMEOUT_SECONDS}s) - protecting agent creation AND chat")
    except (AttributeError, ValueError, OSError) as sig_err:
        # Signal not available (Windows or background thread)
        debug_log(f"OS-level timeout not available: {sig_err}. Using threading timeout instead.")
        signal_obj = None
    
    try:
        debug_log("STEP 1: Creating hotel matcher agent (PROTECTED BY TIMEOUT)...")
        assistant = create_hotel_matcher_agent(llm_model=llm_model)
        debug_log("Agent created successfully")
        
        debug_log("STEP 2: Creating UserProxyAgent...")
        # New autogen_agentchat API uses different parameters
        try:
            user = UserProxyAgent(
                name="HotelMatchUser",
                code_execution_config=False,
                human_input_mode="NEVER",
            )
            debug_log("UserProxyAgent created (standard API)")
        except TypeError:
            # New API (autogen_agentchat) - simplified parameters
            user = UserProxyAgent(name="HotelMatchUser")
            debug_log("UserProxyAgent created (new API)")
        
        user_message = "Here are the hotel search requirements:\n"
        user_message += f"{json.dumps(requirements, indent=2)}\n\n"
        debug_log(f"User message prepared: {user_message[:200]}...")
        
        # Add SOW requirements if available
        if sow_requirements:
            user_message += "**SOW REQUIREMENTS FOR HOTEL ANALYSIS:**\n"
        user_message += f"{json.dumps(sow_requirements, indent=2)}\n\n"
        user_message += (
            "IMPORTANT: Analyze each hotel against these SOW requirements:\n"
            "- Lodging Requirements (room counts, cancellation policy, amenities)\n"
            "- Transportation Requirements (distance to venue, transportation options)\n"
            "- Location Requirements (ZIP codes, proximity to stadium/venue)\n"
            "- Period of Performance (date range availability)\n"
            "- Price competitiveness\n\n"
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

        user_message += "\n\n**CRITICAL INSTRUCTIONS:**\n"
        user_message += "1. You MUST call the `amadeus_search_hotels_tool` function with the provided parameters (city_code, check_in, check_out, adults).\n"
        user_message += "2. **IF NO HOTELS ARE FOUND:**\n"
        user_message += "   - Do NOT return an empty message.\n"
        user_message += "   - Do NOT apologize in plain text.\n"
        user_message += "   - YOU MUST RETURN A VALID JSON with an empty 'hotels' list and a 'reasoning' field explaining why (e.g., 'Dates are too far in the future for booking').\n"
        user_message += "   - Example Failure Response: {\"hotels\": [], \"reasoning\": \"Amadeus API returned no results. The check-in date (2026) is likely outside the available booking window (typically 330 days).\", \"requirements_analysis\": {...}}\n"
        user_message += "3. **IF HOTELS ARE FOUND:**\n"
        user_message += "   - You MUST process ALL offers returned by the Amadeus tool.\n"
        user_message += "   - Analyze each hotel against the SOW requirements provided.\n"
        user_message += "   - Score hotels based on how well they match the requirements.\n"
        user_message += "   - Return a ranked list of hotels with detailed analysis in JSON format.\n"
        user_message += "4. NEVER return empty content - always return valid JSON even if no hotels are found.\n"
        user_message += "5. Use the Amadeus tool to fetch hotels and analyze them against the SOW requirements. Respond strictly with JSON as described in the system prompt.\n"
        user_message += "6. **CRITICAL:** Your response MUST be valid JSON. Start with '{' and end with '}'. Include at minimum: {\"hotels\": [], \"reasoning\": \"...\"}\n"
        user_message += "7. **ABSOLUTELY FORBIDDEN:** Do NOT return an empty string, empty message, or plain text. ALWAYS return valid JSON.\n"
        
        logger.info("Starting hotel matcher chat...")
        logger.info(f"User message length: {len(user_message)}")
        
        # Track start time for latency
        start_time = time.time()
    
        debug_log("STEP 2: Creating UserProxyAgent...")
        # New autogen_agentchat API uses different parameters
        try:
            user = UserProxyAgent(
                name="HotelMatchUser",
                code_execution_config=False,
                human_input_mode="NEVER",
            )
            debug_log("UserProxyAgent created (standard API)")
        except TypeError:
            # New API (autogen_agentchat) - simplified parameters
            user = UserProxyAgent(name="HotelMatchUser")
            debug_log("UserProxyAgent created (new API)")
        
        debug_log("STEP 3: Initiating chat with agent (PROTECTED BY TIMEOUT)...")
        user.initiate_chat(assistant, message=user_message)
        debug_log("Chat initiated successfully")
        
        # Disable alarm if it was set
        if signal_obj:
            try:
                signal_obj.alarm(0)
                debug_log("Timeout alarm disabled (success)")
            except:
                pass
        
        debug_log("STEP 4: Retrieving last message...")
        last_message = assistant.last_message()
        
        if last_message:
            debug_log(f"Last message retrieved: {type(last_message)}")
            debug_log(f"Last message keys: {list(last_message.keys()) if isinstance(last_message, dict) else 'Not a dict'}")
        else:
            debug_log("Last message is None - will trigger fallback")
        
        # Add SOW requirements if available
        if sow_requirements:
            user_message += "**SOW REQUIREMENTS FOR HOTEL ANALYSIS:**\n"
            user_message += f"{json.dumps(sow_requirements, indent=2)}\n\n"
            user_message += (
                "IMPORTANT: Analyze each hotel against these SOW requirements:\n"
                "- Lodging Requirements (room counts, cancellation policy, amenities)\n"
                "- Transportation Requirements (distance to venue, transportation options)\n"
                "- Location Requirements (ZIP codes, proximity to stadium/venue)\n"
                "- Period of Performance (date range availability)\n"
                "- Price competitiveness\n\n"
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

        user_message += "\n\n**CRITICAL INSTRUCTIONS:**\n"
        user_message += "1. You MUST call the `amadeus_search_hotels_tool` function with the provided parameters (city_code, check_in, check_out, adults).\n"
        user_message += "2. **IF NO HOTELS ARE FOUND:**\n"
        user_message += "   - Do NOT return an empty message.\n"
        user_message += "   - Do NOT apologize in plain text.\n"
        user_message += "   - YOU MUST RETURN A VALID JSON with an empty 'hotels' list and a 'reasoning' field explaining why (e.g., 'Dates are too far in the future for booking').\n"
        user_message += "   - Example Failure Response: {\"hotels\": [], \"reasoning\": \"Amadeus API returned no results. The check-in date (2026) is likely outside the available booking window (typically 330 days).\", \"requirements_analysis\": {...}}\n"
        user_message += "3. **IF HOTELS ARE FOUND:**\n"
        user_message += "   - You MUST process ALL offers returned by the Amadeus tool.\n"
        user_message += "   - Analyze each hotel against the SOW requirements provided.\n"
        user_message += "   - Score hotels based on how well they match the requirements.\n"
        user_message += "   - Return a ranked list of hotels with detailed analysis in JSON format.\n"
        user_message += "4. NEVER return empty content - always return valid JSON even if no hotels are found.\n"
        user_message += "5. Use the Amadeus tool to fetch hotels and analyze them against the SOW requirements. Respond strictly with JSON as described in the system prompt.\n"
        user_message += "6. **CRITICAL:** Your response MUST be valid JSON. Start with '{' and end with '}'. Include at minimum: {\"hotels\": [], \"reasoning\": \"...\"}\n"
        user_message += "7. **ABSOLUTELY FORBIDDEN:** Do NOT return an empty string, empty message, or plain text. ALWAYS return valid JSON.\n"
        
        logger.info("Starting hotel matcher chat...")
        logger.info(f"User message length: {len(user_message)}")
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        debug_log(f"Latency: {latency_ms}ms")
        
        logger.info(f"Chat completed. Last message exists: {last_message is not None}")
        
    except (GlobalTimeoutError, Exception) as e:
        # CRITICAL: Catch ALL exceptions including timeout
        if signal_obj:
            try:
                signal_obj.alarm(0)  # Ensure alarm is off
            except:
                pass
        
        debug_log(f"!!! CRITICAL FAILURE: {type(e).__name__}: {e} !!!")
        debug_log("Redirecting to MANUAL FALLBACK...")
        import traceback
        debug_log(f"TRACEBACK: {traceback.format_exc()}")
        return _execute_manual_fallback(requirements, f"System Crash/Timeout: {type(e).__name__}: {str(e)}")
    
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        debug_log(f"Latency: {latency_ms}ms")
        
        logger.info(f"Chat completed. Last message exists: {last_message is not None}")
    
    # Debug: Check chat messages if last_message is None
    if not last_message:
        logger.warning("last_message is None, checking chat_messages...")
        try:
            if hasattr(assistant, 'chat_messages') and assistant.chat_messages:
                logger.info(f"Found {len(assistant.chat_messages)} chat messages")
                for idx, msg in enumerate(assistant.chat_messages[-3:]):  # Last 3 messages
                    logger.info(f"Message {idx}: {type(msg)} - {str(msg)[:200]}")
                    if hasattr(msg, 'get'):
                        logger.info(f"  Content: {msg.get('content', 'N/A')[:200]}")
            elif hasattr(user, 'chat_messages') and user.chat_messages:
                logger.info(f"Found {len(user.chat_messages)} user chat messages")
                for idx, msg in enumerate(user.chat_messages[-3:]):
                    logger.info(f"User Message {idx}: {type(msg)} - {str(msg)[:200]}")
        except Exception as debug_exc:
            logger.warning(f"Error checking chat_messages: {debug_exc}")
    
    # Log LLM call to database if agent_run_id is provided
    if LLM_LOGGER_AVAILABLE and agent_run_id:
        try:
            db = SessionLocal()
            try:
                # Extract prompt (first 50000 chars)
                prompt_text = user_message[:50000] if len(user_message) > 50000 else user_message
                
                # Extract response
                content = last_message.get("content", "") if last_message else ""
                if isinstance(content, list):
                    content = content[0].get("text", "") if content else ""
                response_text = str(content)[:100000] if content else ""  # Limit response size
                
                # Try to extract token usage from message metadata if available
                prompt_tokens = None
                completion_tokens = None
                total_tokens = None
                if last_message and isinstance(last_message, dict):
                    # Check for token usage in metadata
                    metadata = last_message.get("metadata", {})
                    if isinstance(metadata, dict):
                        usage = metadata.get("usage", {})
                        if isinstance(usage, dict):
                            prompt_tokens = usage.get("prompt_tokens")
                            completion_tokens = usage.get("completion_tokens")
                            total_tokens = usage.get("total_tokens")
                
                # Log the LLM call
                log_llm_call(
                    db=db,
                    provider="openai",
                    model=llm_model,
                    prompt=prompt_text,
                    response_text=response_text,
                    agent_run_id=agent_run_id,
                    agent_name="HotelMatcherAgent",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    latency_ms=latency_ms,
                )
                logger.info(f"Logged LLM call to database for agent_run_id={agent_run_id}")
            finally:
                db.close()
        except Exception as log_exc:
            logger.warning(f"Failed to log LLM call to database: {log_exc}", exc_info=True)
        if not last_message:
            debug_log("!!! AGENT FAILED: No output from agent !!!")
            debug_log("SWITCHING TO MANUAL FALLBACK...")
            return _execute_manual_fallback(requirements, "Agent returned no output")
    
    debug_log("Extracting content from last message...")
    content = last_message.get("content")
    debug_log(f"Content type: {type(content)}")
    debug_log(f"Content preview: {str(content)[:500] if content else 'None'}...")
    
    # Handle different content formats
    if isinstance(content, list):
        debug_log(f"Content is a list with {len(content)} items")
        content = content[0].get("text") if content and len(content) > 0 else ""
        debug_log(f"Extracted text from list: {str(content)[:500] if content else 'None'}...")
    elif isinstance(content, dict):
        debug_log("Content is a dict, returning as-is")
        # Already a dict, return as-is
        return content
    
    # Helper function to convert Amadeus offers to hotel match format
    def _convert_amadeus_offers_to_hotels(offers, city_code, check_in, check_out):
        """Convert Amadeus API offers to hotel match format with FILE DEBUGGING."""
        debug_log("\n" + "="*70)
        debug_log(f"FALLBACK PATH ENTERED: _convert_amadeus_offers_to_hotels with {len(offers)} offers")
        debug_log("="*70)
        
        try:
            hotels = []
            
            for idx, offer_data in enumerate(offers):
                debug_log(f"FALLBACK processing offer #{idx+1}")
                
                # CRITICAL FIX: Priority 1 - Raw Amadeus Structure (offer['hotel']['name'])
                # This fixes the "Unknown Hotel" issue seen in logs
                hotel_name = None
                
                # CRITICAL: Check offer.hotel.name FIRST (most common structure)
                if isinstance(offer_data, dict):
                    hotel_obj = offer_data.get("hotel")
                    if isinstance(hotel_obj, dict):
                        hotel_name = hotel_obj.get("name")
                        if hotel_name and isinstance(hotel_name, str) and len(hotel_name.strip()) > 0 and "Unknown" not in hotel_name:
                            debug_log(f"FALLBACK: Found name at offer.hotel.name (PRIORITY 1): '{hotel_name}'")
                            hotel_name = hotel_name.strip()
                # 1. DEBUG: Log the EXACT structure
                if idx == 0:
                    debug_log(f"FALLBACK: INSPECTING OFFER #1 TYPE: {type(offer_data)}")
                    try:
                        raw_dump = json.dumps(offer_data, default=str)
                        debug_log(f"FALLBACK: RAW DATA (first 500 chars): {raw_dump[:500]}")
                        if isinstance(offer_data, dict):
                            debug_log(f"FALLBACK: KEYS: {list(offer_data.keys())}")
                    except Exception as e:
                        debug_log(f"FALLBACK: COULD NOT DUMP JSON: {e}")

                # --- INTERNAL HELPER: Recursive Name Search ---
                def find_name_recursive_fallback(obj, depth=0, max_depth=4):
                    if depth > max_depth: return None
                    if isinstance(obj, dict):
                        # Priority keys
                        for key in ['name', 'hotelName', 'propertyName']:
                            val = obj.get(key)
                            if val and isinstance(val, str) and len(val) > 1 and "Unknown" not in val:
                                return val
                        # Dig deeper
                        for val in obj.values():
                            if isinstance(val, (dict, list)):
                                res = find_name_recursive_fallback(val, depth + 1, max_depth)
                                if res: return res
                    elif isinstance(obj, list):
                        for item in obj:
                            res = find_name_recursive_fallback(item, depth + 1, max_depth)
                            if res: return res
                    return None
                # -----------------------------------------------

                # 2. EXTRACTION STRATEGY (Priority order updated)
                # Attempt 1: Root Level (Processed Client Data)
                if not hotel_name and isinstance(offer_data, dict):
                    hotel_name = offer_data.get("name")
                    if hotel_name:
                        debug_log(f"FALLBACK: Found name at ROOT (PRIORITY 2): '{hotel_name}'")

                # Attempt 2: offer.offer.hotel.name (Nested offer structure)
                if not hotel_name and isinstance(offer_data, dict):
                    try:
                        offer_obj = offer_data.get("offer")
                        if isinstance(offer_obj, dict):
                            nested_hotel = offer_obj.get("hotel")
                            if isinstance(nested_hotel, dict):
                                hotel_name = nested_hotel.get("name")
                                if hotel_name and isinstance(hotel_name, str) and len(hotel_name.strip()) > 0 and "Unknown" not in hotel_name:
                                    debug_log(f"FALLBACK: Found name at offer.offer.hotel.name: '{hotel_name}'")
                                    hotel_name = hotel_name.strip()
                    except Exception as e:
                        debug_log(f"FALLBACK: Error checking offer.offer.hotel.name: {e}")

                # Attempt 3: Deep Search
                if not hotel_name:
                    debug_log(f"FALLBACK: Name missing via standard paths. Trying Deep Search...")
                    hotel_name = find_name_recursive_fallback(offer_data)
                    if hotel_name:
                        debug_log(f"FALLBACK: Deep Search RECOVERED name: '{hotel_name}'")

                # Final Fallback - Try one more recursive search before giving up
                if not hotel_name:
                    debug_log(f"FALLBACK: Name still missing after all attempts. Trying final recursive search...")
                    hotel_name = find_name_recursive_fallback(offer_data, max_depth=6)  # Increase depth
                    if hotel_name:
                        debug_log(f"FALLBACK: Final recursive search RECOVERED name: '{hotel_name}'")
                    else:
                        hotel_name = "N/A"
                        keys = list(offer_data.keys()) if isinstance(offer_data, dict) else 'Not a dict'
                        debug_log(f"FALLBACK: Name FAILED after all attempts. Keys: {keys}")
                        if isinstance(offer_data, dict):
                            try:
                                debug_log(f"FALLBACK: Full offer_data (first 500 chars): {json.dumps(offer_data, default=str)[:500]}")
                            except:
                                pass

                # 3. PRICE extraction
                total_price = 0
                try:
                    if isinstance(offer_data, dict):
                        price_data = offer_data.get("price")
                        if isinstance(price_data, dict):
                            total_price = float(price_data.get("total", 0))
                        elif not price_data:
                            total_price = float(offer_data.get("offer", {}).get("price", {}).get("total", 0))
                except:
                    total_price = 0

                # 4. Construct Hotel Object
                if hotel_name:
                    debug_log(f"FALLBACK: Final hotel_name for offer #{idx+1}: '{hotel_name}'")
                hotel = {
                    "name": str(hotel_name),
                    "address": "See details",
                    "city": city_code,
                    "price_per_night": round(total_price, 2),
                    "total_price": round(total_price, 2),
                    "distance": "Unknown",
                    "rating": 0,
                    "score": 0.7,
                    "reasoning": "Fallback path used",
                    "offer": offer_data 
                }
                hotels.append(hotel)
            debug_log(f"FALLBACK: Returning {len(hotels)} hotels")
            return hotels
        except Exception as e:
            debug_log(f"FALLBACK ERROR: {e}")
            import traceback
            debug_log(f"FALLBACK TRACEBACK: {traceback.format_exc()}")
            return []
    
    # Validate content exists and is not empty
    # Check for empty string, None, or whitespace-only content
    if not content or (isinstance(content, str) and not content.strip()):
        logger.error("Hotel matcher returned empty content - using fallback: direct Amadeus API call")
        
        # FALLBACK: If agent returns empty, call Amadeus API directly
        try:
            from ..services.amadeus_client import search_hotels_by_city_code
            
            city_code = requirements.get("city_code")
            check_in = requirements.get("check_in")
            check_out = requirements.get("check_out")
            adults = requirements.get("adults", 2)
            
            if city_code and check_in and check_out:
                logger.info(f"Fallback: Calling Amadeus API directly - city={city_code}, check_in={check_in}, check_out={check_out}, adults={adults}")
                offers = search_hotels_by_city_code(city_code, check_in, check_out, adults, max_results=10)
                
                if offers:
                    logger.info(f"Fallback: Amadeus API returned {len(offers)} hotels")
                    print(f"\n>>> CALLING _convert_amadeus_offers_to_hotels with {len(offers)} offers", flush=True)
                    if offers:
                        print(f">>> First offer type: {type(offers[0])}", flush=True)
                        print(f">>> First offer has 'name': {'name' in offers[0] if isinstance(offers[0], dict) else 'N/A'}", flush=True)
                        if isinstance(offers[0], dict):
                            print(f">>> First offer name value: {offers[0].get('name')}", flush=True)
                    debug_log(f"FALLBACK (JSON parse error): Amadeus API returned {len(offers)} hotels")
                    if offers and isinstance(offers[0], dict):
                        debug_log(f"FALLBACK (JSON parse error): First offer keys: {list(offers[0].keys())[:10]}")
                    hotels = _convert_amadeus_offers_to_hotels(offers, city_code, check_in, check_out)
                    debug_log(f"FALLBACK (JSON parse error): _convert returned {len(hotels)} hotels")
                    if hotels:
                        debug_log(f"FALLBACK (JSON parse error): First hotel name from _convert: {hotels[0].get('name')}")
                    
                    return {
                        "hotels": hotels,
                        "reasoning": f"Agent returned empty response. Used fallback: Direct Amadeus API call found {len(hotels)} hotels. Hotels were not analyzed against SOW requirements due to agent failure.",
                        "requirements_analysis": {
                            "lodging_requirements_met": False,
                            "transportation_requirements_met": False,
                            "amenities_requirements_met": False,
                            "summary": f"Found {len(hotels)} hotels via fallback (agent failed to process)"
                        },
                        "fallback_used": True
                    }
                else:
                    logger.warning("Fallback: Amadeus API returned no hotels")
            else:
                logger.warning(f"Fallback: Missing required parameters - city_code={city_code}, check_in={check_in}, check_out={check_out}")
        except Exception as fallback_exc:
            logger.error(f"Fallback mechanism failed: {fallback_exc}", exc_info=True)
        
        # If fallback also fails, return error
        return {
            "error": "Hotel matcher returned empty response and fallback mechanism failed",
            "hotels": [],
            "reasoning": "The agent returned an empty message and direct Amadeus API call also failed or returned no results",
            "requirements_analysis": {
                "lodging_requirements_met": False,
                "transportation_requirements_met": False,
                "amenities_requirements_met": False,
                "summary": "No hotels found due to empty response and fallback failure"
            }
        }
    
    # Convert to string if needed
    if not isinstance(content, str):
        content = str(content)
    
    # CRITICAL: Log raw agent response for debugging
    logger.info(f"[Agent Response] Raw content length: {len(content)} chars")
    logger.info(f"[Agent Response] Content preview (first 500 chars): {content[:500]}")
    if len(content) > 500:
        logger.info(f"[Agent Response] Content preview (last 200 chars): {content[-200:]}")
    
    # Robust JSON extraction function
    def extract_json_from_response(response_text: str):
        """
        Extract and parse JSON from agent response.
        Handles:
        1. Markdown code blocks (```json ... ``` or ``` ... ```)
        2. Plain JSON strings
        3. JSON with extra text before/after
        4. Multiple JSON objects (takes first valid one)
        """
        import re
        
        if not response_text or not isinstance(response_text, str):
            return None
        
        # Step 1: Try to extract from markdown code blocks
        # Pattern: ```json ... ``` or ``` ... ```
        markdown_patterns = [
            r"```json\s*(.*?)\s*```",  # ```json ... ```
            r"```\s*(.*?)\s*```",      # ``` ... ```
        ]
        
        for pattern in markdown_patterns:
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                json_str = match.group(1).strip()
                try:
                    parsed = json.loads(json_str)
                    if isinstance(parsed, dict):
                        logger.info(f"[JSON Extraction] Successfully extracted JSON from markdown block")
                        return parsed
                except json.JSONDecodeError:
                    continue
        
        # Step 2: Try to find JSON object in text (handles cases with extra text)
        # Look for {...} pattern - use balanced brace matching
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(response_text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx >= 0:
                    json_str = response_text[start_idx:i+1]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict) and ("hotels" in parsed or "reasoning" in parsed):
                            logger.info(f"[JSON Extraction] Successfully extracted JSON object from text (balanced braces)")
                            return parsed
                    except json.JSONDecodeError:
                        pass
                    start_idx = -1
        
        # Step 3: Try direct JSON parse (if content is already clean JSON)
        content_stripped = response_text.strip()
        if content_stripped.startswith("{") or content_stripped.startswith("["):
            try:
                parsed = json.loads(content_stripped)
                if isinstance(parsed, dict):
                    logger.info(f"[JSON Extraction] Successfully parsed direct JSON")
                    return parsed
            except json.JSONDecodeError:
                pass
        
        return None
    
    # Extract JSON from response
    debug_log("\n" + "="*70)
    debug_log(f"RUN STARTED: run_hotel_match_for_opportunity")
    debug_log(f"AGENT RAW RESPONSE (First 200 chars): {content[:200] if content else 'EMPTY'}")
    debug_log("="*70)
    
    parsed = extract_json_from_response(content)
    
    if parsed:
        # Successfully extracted JSON
        debug_log(f"MAIN PATH: JSON parsed successfully. Keys: {list(parsed.keys())}")
        logger.info(f"[Agent Response] Successfully parsed JSON. Keys: {list(parsed.keys())}")
        
        # CRITICAL: Normalize hotel names in parsed response
        if "hotels" in parsed and isinstance(parsed["hotels"], list):
            
            # --- HELPER: Recursive Name Search (Ana Akış İçin) ---
            def find_name_recursive_main(obj, depth=0, max_depth=4):
                if depth > max_depth: return None
                if isinstance(obj, dict):
                    # Priority keys
                    for key in ['name', 'hotelName', 'hotel_name', 'propertyName']:
                        val = obj.get(key)
                        if val and isinstance(val, str) and len(val) > 1 and "Unknown" not in val:
                            return val
                    # Dig deeper
                    for val in obj.values():
                        if isinstance(val, (dict, list)):
                            res = find_name_recursive_main(val, depth + 1, max_depth)
                            if res: return res
                elif isinstance(obj, list):
                    for item in obj:
                        res = find_name_recursive_main(item, depth + 1, max_depth)
                        if res: return res
                return None
            # -------------------------------------------------------

            normalized_hotels = []
            for i, hotel in enumerate(parsed["hotels"]):
                if not isinstance(hotel, dict):
                    continue
                
                # STRATEGY 1: Direct Access
                hotel_name = hotel.get("name")
                
                # STRATEGY 2: Common Agent Structures
                if not hotel_name or "Unknown" in str(hotel_name):
                     hotel_name = hotel.get("hotel_name") or hotel.get("hotelName")
                
                if not hotel_name:
                    if isinstance(hotel.get("hotel"), dict):
                        hotel_name = hotel.get("hotel", {}).get("name")
                
                # STRATEGY 3: DEEP SEARCH (The Fix)
                # Eğer hala bulamadıysak, JSON ağacının derinliklerine in
                if not hotel_name or "Unknown" in str(hotel_name):
                    debug_log(f"MAIN PATH: Name missing for hotel #{i+1}, trying recursive...")
                    logger.info(f"[Main Logic] Name missing for Hotel #{i+1}. Running Deep Search on Agent Response...")
                    
                    found_name = find_name_recursive_main(hotel)
                    if found_name:
                        hotel_name = found_name
                        debug_log(f"MAIN PATH: Recovered name: {hotel_name}")
                        logger.info(f"[Main Logic] Deep Search RECOVERED: {hotel_name}")
                    else:
                        debug_log(f"MAIN PATH: Failed to recover name.")
                        try:
                            debug_log(f"MAIN PATH: FAILED STRUCTURE (first 500 chars): {json.dumps(hotel, default=str)[:500]}")
                        except:
                            pass

                # Construct Normalized Object
                normalized_hotel = hotel.copy()
                if hotel_name:
                    normalized_hotel["name"] = str(hotel_name)
                    debug_log(f"MAIN PATH: Final hotel_name for hotel #{i+1}: '{hotel_name}'")
                else:
                    # Try to extract from nested structures if name is missing
                    if isinstance(hotel.get("offer"), dict):
                        hotel_name = hotel.get("offer", {}).get("name") or hotel.get("offer", {}).get("hotel", {}).get("name")
                    if not hotel_name and isinstance(hotel.get("hotel"), dict):
                        hotel_name = hotel.get("hotel", {}).get("name")
                    
                    if hotel_name:
                        normalized_hotel["name"] = str(hotel_name)
                        debug_log(f"MAIN PATH: Recovered name from nested structure: '{hotel_name}'")
                    elif "name" not in normalized_hotel or "Unknown" in str(normalized_hotel.get("name", "")):
                        # If name is still missing or contains "Unknown", try recursive search
                        found_name = find_name_recursive_main(hotel)
                        if found_name:
                            normalized_hotel["name"] = str(found_name)
                            debug_log(f"MAIN PATH: Recovered name via recursive search: '{found_name}'")
                        else:
                            normalized_hotel["name"] = "N/A"
                            debug_log(f"MAIN PATH: Could not recover name for hotel #{i+1}, using 'N/A'")
                
                normalized_hotels.append(normalized_hotel)
            
            parsed["hotels"] = normalized_hotels
            logger.info(f"[Agent Response] Normalized {len(normalized_hotels)} hotels")
        
        return parsed
    
    # JSON extraction failed - try fallback
    debug_log("TRIGGERING FALLBACK due to empty/invalid JSON")
    debug_log("SWITCHING TO MANUAL FALLBACK...")
    logger.warning(f"[Agent Response] Failed to extract JSON from response. Content preview: {content[:500]}")
    
    # Check if content looks like JSON (starts with { or [)
    content_stripped = content.strip()
    if not (content_stripped.startswith("{") or content_stripped.startswith("[")):
        # Agent returned plain text instead of JSON - this is the critical error case
        logger.warning(f"Hotel matcher returned plain text instead of JSON. Content preview: {content[:200]}")
        # Return error response
        return {
            "error": f"Agent returned plain text instead of JSON. Message: {content[:500]}",
            "hotels": [],
            "reasoning": "The agent did not follow the JSON output format requirement",
            "requirements_analysis": {
                "lodging_requirements_met": False,
                "transportation_requirements_met": False,
                "amenities_requirements_met": False,
                "summary": "No hotels found - agent output format error"
            }
        }
    
    # Try to parse JSON directly (last attempt)
    try:
        parsed = json.loads(content)
        # Validate it's a dict (not a list or other type)
        if not isinstance(parsed, dict):
            logger.warning(f"Hotel matcher returned JSON but not a dict: {type(parsed)}")
            return {
                "error": "Agent returned invalid JSON structure (expected object, got array or other)",
                "hotels": [],
                "reasoning": "The agent returned JSON in an unexpected format",
                "requirements_analysis": {
                    "lodging_requirements_met": False,
                    "transportation_requirements_met": False,
                    "amenities_requirements_met": False,
                    "summary": "No hotels found - invalid JSON structure"
                }
            }
        return parsed
    except json.JSONDecodeError as exc:
        # JSON parse error - log the actual content for debugging
        logger.error(f"Failed to parse hotel matcher output as JSON. Error: {exc}")
        logger.error(f"Content preview (first 500 chars): {content[:500]}")
        logger.error(f"Content length: {len(content)}")
        
        # JSON parse failed - try fallback mechanism
        logger.warning("JSON parse failed - attempting fallback: direct Amadeus API call")
        try:
            from ..services.amadeus_client import search_hotels_by_city_code
            
            city_code = requirements.get("city_code")
            check_in = requirements.get("check_in")
            check_out = requirements.get("check_out")
            adults = requirements.get("adults", 2)
            
            if city_code and check_in and check_out:
                logger.info(f"Fallback (JSON parse error): Calling Amadeus API directly - city={city_code}, check_in={check_in}, check_out={check_out}, adults={adults}")
                offers = search_hotels_by_city_code(city_code, check_in, check_out, adults, max_results=10)
                
                if offers:
                    logger.info(f"Fallback (JSON parse error): Amadeus API returned {len(offers)} hotels")
                    print(f"\n>>> CALLING _convert_amadeus_offers_to_hotels with {len(offers)} offers", flush=True)
                    if offers:
                        print(f">>> First offer type: {type(offers[0])}", flush=True)
                        print(f">>> First offer has 'name': {'name' in offers[0] if isinstance(offers[0], dict) else 'N/A'}", flush=True)
                        if isinstance(offers[0], dict):
                            print(f">>> First offer name value: {offers[0].get('name')}", flush=True)
                    debug_log(f"FALLBACK (JSON parse error): Amadeus API returned {len(offers)} hotels")
                    if offers and isinstance(offers[0], dict):
                        debug_log(f"FALLBACK (JSON parse error): First offer keys: {list(offers[0].keys())[:10]}")
                    hotels = _convert_amadeus_offers_to_hotels(offers, city_code, check_in, check_out)
                    debug_log(f"FALLBACK (JSON parse error): _convert returned {len(hotels)} hotels")
                    if hotels:
                        debug_log(f"FALLBACK (JSON parse error): First hotel name from _convert: {hotels[0].get('name')}")
                    
                    return {
                        "hotels": hotels,
                        "reasoning": f"Agent returned invalid JSON. Used fallback: Direct Amadeus API call found {len(hotels)} hotels. Hotels were not analyzed against SOW requirements due to agent JSON parse error.",
                        "requirements_analysis": {
                            "lodging_requirements_met": False,
                            "transportation_requirements_met": False,
                            "amenities_requirements_met": False,
                            "summary": f"Found {len(hotels)} hotels via fallback (agent JSON parse error)"
                        },
                        "fallback_used": True
                    }
        
        except Exception as fallback_exc:
            logger.error(f"Fallback mechanism failed during JSON parse error: {fallback_exc}", exc_info=True)
        
        # Return graceful error response instead of crashing
        return {
            "error": f"Failed to parse agent response as JSON: {str(exc)}",
            "hotels": [],
            "reasoning": f"The agent's response could not be parsed. This may indicate missing city_code or API error. Raw response preview: {content[:200]}",
            "requirements_analysis": {
                "lodging_requirements_met": False,
                "transportation_requirements_met": False,
                "amenities_requirements_met": False,
                "summary": "No hotels found - JSON parsing error"
            }
        }
    except Exception as exc:
        # Unexpected error
        logger.error(f"Unexpected error parsing hotel matcher output: {exc}", exc_info=True)
        return {
            "error": f"Unexpected error: {str(exc)}",
            "hotels": [],
            "reasoning": "An unexpected error occurred while processing the agent's response",
            "requirements_analysis": {
                "lodging_requirements_met": False,
                "transportation_requirements_met": False,
                "amenities_requirements_met": False,
                "summary": "No hotels found - unexpected error"
            }
        }

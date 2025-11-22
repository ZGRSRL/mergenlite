"""
AutoGen-based hotel matcher agent that queries Amadeus and returns scored hotels.
"""
from __future__ import annotations

import json
import logging
import time
import re
from typing import Any, Dict, Optional

from ..services.amadeus_client import search_hotels_by_city_code

logger = logging.getLogger(__name__)

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
    if not AUTOGEN_AVAILABLE:
        raise HotelMatcherUnavailableError("pyautogen not installed. Run `pip install pyautogen`.")

    import os
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY")
    
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

    # Use llm_config with autogen (standard API)
    # autogen 0.10.x supports llm_config, not direct model parameter
    try:
        # First try with tools if available
        if AUTOGEN_AVAILABLE and tool is not None:
            try:
                assistant = AssistantAgent(
                    name="HotelMatcherAgent",
                    system_message=system_message,
                    llm_config=llm_config,
                    tools=[amadeus_search_hotels_tool],
                )
                logger.info("HotelMatcherAgent created with tools")
            except TypeError:
                # Tools not supported, try without
                logger.warning("AssistantAgent rejected tools parameter; retrying without tools")
                assistant = AssistantAgent(
                    name="HotelMatcherAgent",
                    system_message=system_message,
                    llm_config=llm_config,
                )
                logger.info("HotelMatcherAgent created without tools")
        else:
            # No tools available, create without
            assistant = AssistantAgent(
                name="HotelMatcherAgent",
                system_message=system_message,
                llm_config=llm_config,
            )
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
    """
    Run hotel matching with SOW requirements analysis.
    
    Args:
        requirements: Basic hotel search requirements (city_code, check_in, check_out, adults)
        decision_hint: Optional decision cache hint
        sow_requirements: SOW analysis requirements (LodgingRequirements, TransportationRequirements, etc.)
        llm_model: LLM model to use
    """
    if not AUTOGEN_AVAILABLE:
        raise HotelMatcherUnavailableError("pyautogen not installed. Run `pip install pyautogen`.")

    assistant = create_hotel_matcher_agent(llm_model=llm_model)
    # New autogen_agentchat API uses different parameters
    try:
        user = UserProxyAgent(
            name="HotelMatchUser",
            code_execution_config=False,
            human_input_mode="NEVER",
        )
    except TypeError:
        # New API (autogen_agentchat) - simplified parameters
        user = UserProxyAgent(name="HotelMatchUser")
    
    user_message = "Here are the hotel search requirements:\n"
    user_message += f"{json.dumps(requirements, indent=2)}\n\n"
    
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
    
    user.initiate_chat(assistant, message=user_message)
    last_message = assistant.last_message()
    
    # Calculate latency
    latency_ms = int((time.time() - start_time) * 1000)
    
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
        logger.error("Hotel matcher produced no output - agent returned None")
        # Try to get any messages from the conversation
        try:
            if hasattr(assistant, 'chat_messages') and assistant.chat_messages:
                last_chat_message = assistant.chat_messages[-1] if assistant.chat_messages else None
                if last_chat_message:
                    logger.warning(f"Found chat message: {last_chat_message}")
        except:
            pass
        
        return {
            "error": "Hotel matcher agent produced no output",
            "hotels": [],
            "reasoning": "The AutoGen agent did not return any response. This may indicate: 1) Agent timeout, 2) LLM API error, 3) Agent configuration issue. Please check logs for details.",
            "requirements_analysis": {
                "lodging_requirements_met": False,
                "transportation_requirements_met": False,
                "amenities_requirements_met": False,
                "summary": "No hotels found due to agent error - agent returned empty response"
            }
        }
    
    content = last_message.get("content")
    
    # Handle different content formats
    if isinstance(content, list):
        content = content[0].get("text") if content and len(content) > 0 else ""
    elif isinstance(content, dict):
        # Already a dict, return as-is
        return content
    
    # Helper function to convert Amadeus offers to hotel match format
    def _convert_amadeus_offers_to_hotels(offers, city_code, check_in, check_out):
        """Convert Amadeus API offers to hotel match format."""
        hotels = []
        for offer_data in offers:
            # CRITICAL FIX: amadeus_client now returns formatted offers with 'name' at root level
            # Structure: {"name": "...", "hotel": {...}, "offer": {...}, "price": {...}, ...}
            
            # Extract hotel name - Priority: root level 'name' (from formatted_offers) > hotel.name > offer.hotel.name > fallback
            hotel_name = offer_data.get("name")  # Root level name (from amadeus_client formatted_offers)
            if not hotel_name:
                # Fallback 1: try hotel.name (for backward compatibility)
                hotel_info = offer_data.get("hotel", {})
                if isinstance(hotel_info, dict):
                    hotel_name = hotel_info.get("name")
            if not hotel_name:
                # Fallback 2: try offer.hotel.name (for raw Amadeus response structure)
                offer_info = offer_data.get("offer", {})
                if isinstance(offer_info, dict):
                    offer_hotel = offer_info.get("hotel", {})
                    if isinstance(offer_hotel, dict):
                        hotel_name = offer_hotel.get("name")
            
            # If still no name found, use "Unknown Hotel" and log for debugging
            if not hotel_name:
                hotel_name = "Unknown Hotel"
                logger.warning(f"Could not extract hotel name from offer_data. Keys: {list(offer_data.keys())}, hotel keys: {list(offer_data.get('hotel', {}).keys()) if isinstance(offer_data.get('hotel'), dict) else 'N/A'}")
            else:
                hotel_name = str(hotel_name)
            
            # Extract hotel info - use nested structure if available, otherwise use root level data
            hotel_info = offer_data.get("hotel", {})
            if not isinstance(hotel_info, dict):
                hotel_info = {}
            
            # Extract offer info
            offer_info = offer_data.get("offer", {})
            if not isinstance(offer_info, dict):
                offer_info = {}
            
            # Extract price - CRITICAL: Check both root level 'price' and nested 'offer.price'
            price_info = offer_data.get("price", {})  # Root level price (from formatted_offers)
            if not price_info or not isinstance(price_info, dict):
                price_info = offer_info.get("price", {})  # Fallback to nested price
            
            # Extract prices - CRITICAL: formatted_offers uses {"total": ..., "currency": ..., "base": ...}
            total_price = float(price_info.get("total", 0)) if price_info.get("total") else 0
            avg_price = 0
            # Try variations first (nested structure), then calculate from total
            if price_info.get("variations", {}).get("average", {}).get("total"):
                avg_price = float(price_info.get("variations", {}).get("average", {}).get("total"))
            elif total_price > 0:
                # Calculate average from total if variations not available
                from datetime import datetime
                try:
                    check_in_dt = datetime.fromisoformat(check_in)
                    check_out_dt = datetime.fromisoformat(check_out)
                    nights = (check_out_dt - check_in_dt).days
                    if nights > 0:
                        avg_price = total_price / nights
                except:
                    pass
            
            # Extract location
            latitude = hotel_info.get("latitude")
            longitude = hotel_info.get("longitude")
            city_code_from_api = hotel_info.get("cityCode", city_code)
            
            # Extract room info
            room_info = offer_info.get("room", {})
            room_description = ""
            if room_info.get("description", {}).get("text"):
                room_description = room_info.get("description", {}).get("text", "")[:200]
            
            hotel = {
                "name": hotel_name,
                "address": f"Lat: {latitude}, Lon: {longitude}" if latitude and longitude else "Address not available",
                "city": city_code_from_api,
                "price_per_night": round(avg_price, 2) if avg_price > 0 else 0,
                "total_price": round(total_price, 2) if total_price > 0 else 0,
                "distance": "Unknown",  # Amadeus doesn't provide distance to venue
                "rating": 0,  # Amadeus doesn't provide rating in this endpoint
                "score": 0.7,  # Default score since we can't analyze against SOW
                "reasoning": f"Hotel found via direct Amadeus API call (agent fallback). {room_description}",
                "offer": offer_data,  # Keep full offer for reference
                "hotel_id": hotel_info.get("hotelId") if hotel_info else None,
                "chain_code": hotel_info.get("chainCode") if hotel_info else None,
            }
            hotels.append(hotel)
        return hotels
    
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
                    hotels = _convert_amadeus_offers_to_hotels(offers, city_code, check_in, check_out)
                    
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
    parsed = extract_json_from_response(content)
    
    if parsed:
        # Successfully extracted JSON
        logger.info(f"[Agent Response] Successfully parsed JSON. Keys: {list(parsed.keys())}")
        
        # CRITICAL: Normalize hotel names in parsed response
        # Handle key variations: name, hotel_name, hotelName, etc.
        if "hotels" in parsed and isinstance(parsed["hotels"], list):
            normalized_hotels = []
            for hotel in parsed["hotels"]:
                if not isinstance(hotel, dict):
                    continue
                
                # Extract hotel name with flexible key matching
                # Priority: name > hotel_name > hotelName > hotel (if string) > hotel.name (if dict)
                hotel_name = hotel.get("name")
                if not hotel_name:
                    hotel_name = hotel.get("hotel_name") or hotel.get("hotelName")
                if not hotel_name:
                    hotel_obj = hotel.get("hotel")
                    if isinstance(hotel_obj, str):
                        hotel_name = hotel_obj
                    elif isinstance(hotel_obj, dict):
                        hotel_name = hotel_obj.get("name")
                
                # If still no name, try to extract from nested structures
                if not hotel_name:
                    # Try amadeus_hotel_id or hotel_id to identify
                    hotel_id = hotel.get("amadeus_hotel_id") or hotel.get("hotel_id") or hotel.get("hotelId")
                    if hotel_id:
                        logger.warning(f"[Hotel Name] Missing name for hotel ID: {hotel_id}")
                
                # Normalize hotel dict
                normalized_hotel = hotel.copy()
                if hotel_name:
                    normalized_hotel["name"] = str(hotel_name)
                elif "name" not in normalized_hotel:
                    normalized_hotel["name"] = "Unknown Hotel"
                    logger.warning(f"[Hotel Name] Could not extract name from hotel: {list(hotel.keys())}")
                
                normalized_hotels.append(normalized_hotel)
            
            parsed["hotels"] = normalized_hotels
            logger.info(f"[Agent Response] Normalized {len(normalized_hotels)} hotels")
        
        return parsed
    
    # JSON extraction failed - try fallback
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
                    hotels = _convert_amadeus_offers_to_hotels(offers, city_code, check_in, check_out)
                    
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

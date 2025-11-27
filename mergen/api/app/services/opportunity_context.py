"""
Helpers to derive structured hotel search requirements from an Opportunity.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..models import Opportunity
from .amadeus_client import lookup_city_code

logger = logging.getLogger(__name__)



def _extract_city_from_title(title: Optional[str]) -> Optional[str]:
    if not title:
        return None
    if "-" in title:
        tail = title.split("-")[-1].strip()
        return tail.split("(")[0].strip()
    return title.strip()


def build_hotel_match_requirements(
    opportunity: Opportunity, 
    options: Optional[Dict[str, Any]] = None,
    sow_analysis: Optional[Dict[str, Any]] = None,
    document_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build a minimal requirement payload for the HotelMatcher agent.
    Priority:
      1. values provided in options (highest priority)
      2. values extracted from SOW analysis (if provided)
      3. values extracted from document analysis (if provided)
      4. values stored on opportunity (cached_data/place_of_performance/etc)
      5. basic fallbacks
    
    Args:
        opportunity: Opportunity model instance
        options: Manual override options (city_code, check_in, check_out, adults, etc.)
        sow_analysis: SOW analysis result containing EventDetails, Location, Dates, etc.
        document_analysis: Document analysis result containing extracted text from PDFs/DOCX
    """
    options = options or {}
    cached = opportunity.cached_data or {}
    
    # Extract from document analysis first (raw text from PDFs/DOCX)
    extracted_text = None
    if document_analysis:
        # Get combined text from all analyzed documents
        analyzed_docs = document_analysis.get("analyzed_documents", [])
        if analyzed_docs:
            extracted_text = " ".join([
                doc.get("extracted_text", "") 
                for doc in analyzed_docs 
                if doc.get("extracted_text")
            ])
        # Also try combined_text_preview if available
        if not extracted_text:
            extracted_text = document_analysis.get("combined_text_preview", "")
    
    # Extract from SOW analysis if available
    event_details = None
    location_info = None
    dates_info = None
    sleeping_rooms = None
    locations_array = None  # Locations table from SOW analysis
    
    logger.info(f"--- BUILDING REQUIREMENTS FOR OPP {opportunity.id} ---")
    logger.info(f"build_hotel_match_requirements called with sow_analysis: {sow_analysis is not None}")
    
    if sow_analysis:
        event_details = sow_analysis.get("EventDetails", {})
        if not event_details:
            # Try alternative key names
            event_details = sow_analysis.get("event_details", {})
        
        location_info = event_details.get("Location", {})
        if not location_info:
            location_info = event_details.get("location", {})
        
        dates_info = event_details.get("Dates", {})
        if not dates_info:
            dates_info = event_details.get("dates", {})
        
        sleeping_rooms = sow_analysis.get("SleepingRoomRequirements", {})
        if not sleeping_rooms:
            sleeping_rooms = sow_analysis.get("sleeping_room_requirements", {})
        
        # CRITICAL: Extract Locations array (table with multiple cities)
        locations_array = sow_analysis.get("Locations", [])
        if not locations_array:
            locations_array = sow_analysis.get("locations", [])
        
        logger.info(f"SOW Analysis Data Loaded. Locations Array Size: {len(locations_array)}")

    # City code: options > opportunity title (extract from title) > document analysis (text extraction) > SOW Locations array (match title) > cached > fallback
    city_code = options.get("city_code")
    city_name = options.get("city_name")
    
    # PRIORITY 0: Extract city from opportunity title FIRST (most specific)
    # This allows us to match the city mentioned in the title with Locations array
    title_city_name = None
    if not city_code and not city_name and opportunity.title:
        title_lower = opportunity.title.lower()
        # Common city patterns in titles
        city_keywords = {
            "houston": "Houston",
            "philadelphia": "Philadelphia",
            "atlanta": "Atlanta",
            "dallas": "Dallas",
            "miami": "Miami",
            "los angeles": "Los Angeles",
            "san francisco": "San Francisco",
            "seattle": "Seattle",
            "boston": "Boston",
            "chicago": "Chicago",
            "new york": "New York",
            "washington": "Washington",
            "kansas city": "Kansas City",
        }
        
        for keyword, city in city_keywords.items():
            if keyword in title_lower:
                title_city_name = city
                logger.info(f"✅ City extracted from opportunity title: {city}")
                break
    
    # PRIORITY 1: Extract city from document text FIRST (before using Locations array)
    # This ensures we use the city mentioned in documents, not just the first city in Locations array
    doc_extracted_city = None
    if not city_code and not city_name and extracted_text:
        # Extract city from document text (will be processed in PRIORITY 2 below)
        # We'll set doc_extracted_city after extraction
        pass
    
    # PRIORITY 1.5: If we have a city from title OR document, find it in Locations array
    # Otherwise, DON'T use Locations array automatically (let document extraction run first)
    first_location = None
    if not city_code and locations_array and isinstance(locations_array, list) and len(locations_array) > 0:
        logger.info(f"Locations array available (length: {len(locations_array)})")
        
        # If we have a city_name from title, try to find matching location in array
        city_to_match = title_city_name or doc_extracted_city
        if city_to_match:
            logger.info(f"Looking for '{city_to_match}' in Locations array...")
            matching_location = None
            for loc in locations_array:
                if isinstance(loc, dict):
                    loc_city = loc.get("city") or loc.get("City")
                    if loc_city and city_to_match.lower() in loc_city.lower():
                        matching_location = loc
                        logger.info(f"✅ Found matching location in array: {loc_city}")
                        break
            
            if matching_location:
                first_location = matching_location
            else:
                logger.warning(f"⚠️ '{city_to_match}' not found in Locations array")
        # If no city to match, DON'T use first location - let document extraction run first
        logger.info(f"Processing First Location: {first_location}")
        logger.info(f"First location type: {type(first_location)}")
        
        if isinstance(first_location, dict):
            # Hangi key'leri içeriyor görelim
            location_keys = list(first_location.keys())
            logger.info(f"Location Keys: {location_keys}")
            
            # Olası tüm anahtarları dene
            possible_city_keys = ["city", "City", "location", "Location", "city_name", "CityName"]
            
            city_name_from_location = None
            for key in possible_city_keys:
                val = first_location.get(key)
                if val:
                    city_name_from_location = val
                    logger.info(f"✅ City Name Found via key '{key}': {city_name_from_location}")
                    break
            
            if city_name_from_location:
                city_name = city_name or city_name_from_location
                # Extract city name (remove state if present, e.g., "Philadelphia, PA" -> "Philadelphia")
                city_clean = re.split(r"[,\-/]", city_name_from_location)[0].strip()
                logger.info(f"Cleaned city name: {city_clean}")
                
                # Lookup City Code
                city_code = lookup_city_code(city_clean)
                logger.info(f"Lookup City Code for '{city_clean}': {city_code}")
                
                # Manuel Fallback (Philadelphia IATA Kodu PHL'dir)
                if not city_code:
                    manual_map = {
                        "philadelphia": "PHL",
                        "atlanta": "ATL",
                        "boston": "BOS",
                        "miami": "MIA",
                        "houston": "HOU",  # Houston city code (not IAH which is airport)
                        "dallas": "DFW",
                        "los angeles": "LAX",
                        "san francisco": "SFO",
                        "seattle": "SEA",
                        "kansas city": "MCI",
                        "new york": "NYC",
                        "chicago": "CHI",
                        "denver": "DEN",
                        "phoenix": "PHX",
                        "tampa": "TPA",
                        "austin": "AUS",
                        "las vegas": "LAS",
                        "washington": "WAS",
                        "detroit": "DTW",
                        "minneapolis": "MSP",
                        "portland": "PDX",
                        "san diego": "SAN",
                        "san antonio": "SAT",
                        "nashville": "BNA",
                        "indianapolis": "IND",
                        "columbus": "CMH",
                        "charlotte": "CLT",
                        "orlando": "MCO",
                        "jacksonville": "JAX",
                    }
                    city_code = manual_map.get(city_clean.lower())
                    if city_code:
                        logger.info(f"✅ City Code found via Manual Map: {city_code}")
                    else:
                        logger.warning(f"❌ City code lookup failed for: {city_clean} (not in manual map)")
            else:
                logger.warning(f"❌ No city field found in first location. Available keys: {location_keys}")
        else:
            logger.warning(f"❌ First location is not a dict: {type(first_location)}")
    
    # PRIORITY 2: Extract city from document text (BEFORE using first location from array)
    # This ensures we use the city mentioned in the actual documents, not just the first city in Locations array
    if not city_code and not city_name and extracted_text:
        # Look for common city patterns in text (more specific patterns)
        city_patterns = [
            # Pattern: "City: Houston" or "Location: Houston, TX"
            r"(?:City|Location|Venue|Meeting\s+Location)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            # Pattern: "Houston, TX" or "New York, NY"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?),\s*(?:TX|CA|NY|FL|IL|GA|WA|CO|AZ|NV|MA|PA|NC|VA|OH|MI|TN|IN|MO|MD|WI|MN|AL|LA|KY|OR|OK|CT|IA|AR|UT|MS|KS|NM|NE|WV|HI|NH|ID|ME|RI|MT|DE|SD|AK|ND|VT|WY|DC)",
            # Pattern: "in Houston" or "at Houston" (but not "in the" or "at the")
            r"(?:in|at|near|located\s+in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?:\s|,|\.|$)",
            # Pattern: "Houston Texas" or "New York New York"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:Texas|California|New\s+York|Florida|Illinois|Georgia|Washington|Colorado|Arizona|Nevada|Massachusetts|Pennsylvania|North\s+Carolina|Virginia|Ohio|Michigan|Tennessee|Indiana|Missouri|Maryland|Wisconsin|Minnesota|Alabama|Louisiana|Kentucky|Oregon|Oklahoma|Connecticut|Iowa|Arkansas|Utah|Mississippi|Kansas|New\s+Mexico|Nebraska|West\s+Virginia|Hawaii|New\s+Hampshire|Idaho|Maine|Rhode\s+Island|Montana|Delaware|South\s+Dakota|Alaska|North\s+Dakota|Vermont|Wyoming|District\s+of\s+Columbia)",
        ]
        # Common US city names to validate against
        known_cities = {
            "Houston", "New York", "Los Angeles", "Chicago", "Phoenix", "Philadelphia", "San Antonio", "San Diego",
            "Dallas", "San Jose", "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte", "San Francisco",
            "Indianapolis", "Seattle", "Denver", "Washington", "Boston", "El Paso", "Detroit", "Nashville", "Portland",
            "Oklahoma City", "Las Vegas", "Memphis", "Louisville", "Baltimore", "Milwaukee", "Albuquerque", "Tucson",
            "Fresno", "Sacramento", "Kansas City", "Mesa", "Atlanta", "Omaha", "Colorado Springs", "Raleigh",
            "Miami", "Long Beach", "Virginia Beach", "Oakland", "Minneapolis", "Tulsa", "Tampa", "Arlington", "New Orleans"
        }
        
        for pattern in city_patterns:
            matches = re.findall(pattern, extracted_text[:10000], re.IGNORECASE)  # Check first 10000 chars
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        potential_city = match[0].strip()
                    else:
                        potential_city = match.strip()
                    
                    # Filter out common false positives
                    false_positives = {
                        "The", "A", "An", "This", "That", "These", "Those", "Meeting", "Event", "Conference",
                        "All", "Any", "Each", "Every", "Some", "Many", "Most", "Few", "Several", "Various",
                        "Designated", "Selected", "Required", "Needed", "Available", "Provided", "Included"
                    }
                    
                    # Check if it's a known city or looks like a city name
                    if (potential_city not in false_positives and 
                        len(potential_city) > 2 and 
                        (potential_city in known_cities or 
                         (potential_city[0].isupper() and len(potential_city.split()) <= 3))):
                        doc_extracted_city = potential_city
                        city_name = potential_city
                        logger.info(f"✅ City extracted from document text: {city_name}")
                        # Try to lookup city code
                        lookup_name = re.split(r"[,\-/]", city_name)[0].strip()
                        city_code = lookup_city_code(lookup_name)
                        if city_code:
                            logger.info(f"✅ City code found: {city_code}")
                            # Now try to find this city in Locations array for dates
                            if locations_array and isinstance(locations_array, list):
                                for loc in locations_array:
                                    if isinstance(loc, dict):
                                        loc_city = loc.get("city") or loc.get("City")
                                        if loc_city and city_name.lower() in loc_city.lower():
                                            first_location = loc
                                            logger.info(f"✅ Found matching location in array for dates: {loc_city}")
                                            break
                            break
                if city_code:
                    break
    
    # PRIORITY 2: Extract city from SOW analysis Location (EventDetails.Location)
    if not city_code and location_info:
        # Extract city from SOW analysis Location
        if isinstance(location_info, dict):
            city_name = city_name or location_info.get("City") or location_info.get("city")
            state = location_info.get("State") or location_info.get("state")
            country = location_info.get("Country") or location_info.get("country")
            if city_name:
                # Try to lookup city code from city name
                lookup_name = re.split(r"[,\-/]", city_name)[0].strip()
                city_code = lookup_city_code(lookup_name)
                if city_code:
                    logger.info(f"City code determined from SOW EventDetails.Location: {lookup_name} -> {city_code}")
    
    if not city_code:
        city_code = cached.get("cityCode")
    
    if not city_name:
        city_name = (
            cached.get("placeOfPerformance")
            or opportunity.place_of_performance
            or _extract_city_from_title(opportunity.title)
        )

    if not city_code and city_name:
        lookup_name = re.split(r"[,\-/]", city_name)[0].strip()
        city_code = lookup_city_code(lookup_name)
        # If lookup failed, try common city mappings as fallback
        if not city_code:
            common_cities = {
                "houston": "HOU", "new york": "NYC", "washington": "WAS", "chicago": "CHI",
                "los angeles": "LAX", "miami": "MIA", "atlanta": "ATL", "dallas": "DFW",
                "boston": "BOS", "seattle": "SEA", "denver": "DEN", "phoenix": "PHX",
                "tampa": "TPA", "austin": "AUS", "san francisco": "SFO", "las vegas": "LAS"
            }
            city_lower = lookup_name.lower().strip()
            city_code = common_cities.get(city_lower)

    if not city_code:
        # Last resort: try to extract from opportunity title
        if opportunity.title:
            title_city = _extract_city_from_title(opportunity.title)
            if title_city:
                city_code = lookup_city_code(title_city)
                if city_code:
                    city_name = title_city
                    logger.warning(f"City code determined from title: {city_name} -> {city_code}")
        
        # DO NOT use default/fallback cities - only use what's found in documents
        if not city_code:
            # Fallback: Eğer hala city code yoksa ve city_name varsa logla
            if city_name:
                logger.warning(f"City Name '{city_name}' found but NO City Code derived! Using fallback.")
                # Try one more time with manual map
                city_clean = re.split(r"[,\-/]", city_name)[0].strip()
                manual_map = {
                    "philadelphia": "PHL", "atlanta": "ATL", "boston": "BOS", "miami": "MIA",
                    "houston": "IAH", "dallas": "DFW", "los angeles": "LAX", "san francisco": "SFO",
                    "seattle": "SEA", "kansas city": "MCI", "new york": "NYC", "chicago": "CHI",
                    "denver": "DEN", "phoenix": "PHX", "tampa": "TPA", "austin": "AUS",
                    "las vegas": "LAS", "washington": "WAS", "detroit": "DTW", "minneapolis": "MSP",
                    "portland": "PDX", "san diego": "SAN", "san antonio": "SAT", "nashville": "BNA",
                    "indianapolis": "IND", "columbus": "CMH", "charlotte": "CLT", "orlando": "MCO",
                    "jacksonville": "JAX",
                }
                city_code = manual_map.get(city_clean.lower())
                if city_code:
                    logger.info(f"✅ City Code found via fallback manual map: {city_code}")
            
            if not city_code:
                raise ValueError(f"City code could not be determined for '{city_name}'; provide options.city_code.")

    # Dates: options > SOW analysis (Locations array or EventDetails) > document analysis (text extraction) > opportunity response_deadline > fallback
    check_in = options.get("check_in")
    check_out = options.get("check_out")
    
    # PRIORITY 1: Extract dates from Locations array (if available)
    if (not check_in or not check_out) and locations_array and isinstance(locations_array, list) and len(locations_array) > 0:
        # Use first location's start_date
        first_location = locations_array[0]
        if isinstance(first_location, dict):
            start_date_str = first_location.get("start_date") or first_location.get("startDate")
            num_days = first_location.get("num_days") or first_location.get("numDays")
            
            if start_date_str and not check_in:
                try:
                    # Parse start date
                    if isinstance(start_date_str, str):
                        # Try ISO format first
                        try:
                            start_dt = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
                            check_in = start_dt.date().isoformat()
                        except:
                            # Try other formats
                            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]:
                                try:
                                    start_dt = datetime.strptime(start_date_str, fmt)
                                    check_in = start_dt.date().isoformat()
                                    break
                                except:
                                    continue
                    
                    # Calculate check_out from start_date + num_days
                    if check_in and num_days and not check_out:
                        try:
                            start_dt = datetime.fromisoformat(check_in)
                            from datetime import timedelta
                            end_dt = start_dt + timedelta(days=int(num_days))
                            check_out = end_dt.date().isoformat()
                        except:
                            pass
                except Exception as e:
                    logger.warning(f"Error parsing dates from Locations array: {e}")
    
    # PRIORITY 2: Extract dates from EventDetails or PeriodOfPerformance
    if (not check_in or not check_out) and event_details:
        if not check_in:
            start_date = event_details.get("start_date") or event_details.get("startDate")
            if start_date:
                try:
                    if isinstance(start_date, str):
                        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        check_in = start_dt.date().isoformat()
                except:
                    pass
        
        if not check_out:
            end_date = event_details.get("end_date") or event_details.get("endDate")
            if end_date:
                try:
                    if isinstance(end_date, str):
                        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        check_out = end_dt.date().isoformat()
                except:
                    pass
    
    # Also check PeriodOfPerformance
    if (not check_in or not check_out) and sow_analysis:
        pop = sow_analysis.get("PeriodOfPerformance", {}) or sow_analysis.get("period_of_performance", {})
        if pop and isinstance(pop, dict):
            if not check_in:
                start_date = pop.get("start_date") or pop.get("startDate")
                if start_date:
                    try:
                        if isinstance(start_date, str):
                            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            check_in = start_dt.date().isoformat()
                    except:
                        pass
            
            if not check_out:
                end_date = pop.get("end_date") or pop.get("endDate")
                if end_date:
                    try:
                        if isinstance(end_date, str):
                            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                            check_out = end_dt.date().isoformat()
                    except:
                        pass
    
    # Try to extract dates from document text if not found in SOW analysis
    if (not check_in or not check_out) and extracted_text:
        # Look for date patterns
        date_patterns = [
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",  # MM/DD/YYYY or DD/MM/YYYY
            r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",  # YYYY/MM/DD
            r"(?:start|begin|check-in|arrival)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(?:end|finish|check-out|departure)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(?:date|dates)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s*(?:to|-|through)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, extracted_text[:5000], re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    # Date range found
                    try:
                        start_str = matches[0][0]
                        end_str = matches[0][1]
                        # Try to parse dates
                        for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                            try:
                                start_dt = datetime.strptime(start_str, fmt)
                                end_dt = datetime.strptime(end_str, fmt)
                                if not check_in:
                                    check_in = start_dt.date().isoformat()
                                if not check_out:
                                    check_out = end_dt.date().isoformat()
                                break
                            except:
                                continue
                    except:
                        pass
                else:
                    # Single date found
                    date_str = matches[0]
                    for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y", "%Y-%m-%d"]:
                        try:
                            date_dt = datetime.strptime(date_str, fmt)
                            if not check_in:
                                check_in = date_dt.date().isoformat()
                            elif not check_out:
                                check_out = date_dt.date().isoformat()
                            break
                        except:
                            continue
                if check_in and check_out:
                    break
    
    if not check_in and dates_info:
        if isinstance(dates_info, dict):
            check_in = dates_info.get("Start") or dates_info.get("start")
            if check_in and isinstance(check_in, str):
                # Ensure ISO format
                try:
                    dt = datetime.fromisoformat(check_in.replace('Z', '+00:00'))
                    check_in = dt.date().isoformat()
                except:
                    pass
    
    if not check_out and dates_info:
        if isinstance(dates_info, dict):
            check_out = dates_info.get("End") or dates_info.get("end")
            if check_out and isinstance(check_out, str):
                try:
                    dt = datetime.fromisoformat(check_out.replace('Z', '+00:00'))
                    check_out = dt.date().isoformat()
                except:
                    pass
    
    if not check_in:
        check_in = _derive_date(opportunity.response_deadline, fallback_days=30)
    if not check_out:
        check_out = _derive_date(opportunity.response_deadline, fallback_days=33)

    if not check_in or not check_out:
        raise ValueError("Check-in/out dates are required; provide options.check_in/check_out.")
    
    # CRITICAL: Limit date range to max 30 days (Amadeus API limitation)
    # If range is longer, use check_in + 30 days as check_out
    try:
        check_in_dt = datetime.fromisoformat(check_in).date()
        check_out_dt = datetime.fromisoformat(check_out).date()
        days_diff = (check_out_dt - check_in_dt).days
        
        if days_diff > 30:
            logger.warning(f"Date range too long ({days_diff} days), limiting to 30 days for Amadeus API")
            check_out_dt = check_in_dt + timedelta(days=30)
            check_out = check_out_dt.isoformat()
            logger.info(f"Adjusted check_out date: {check_out} (was {datetime.fromisoformat(check_out).date().isoformat()})")
    except Exception as e:
        logger.warning(f"Error calculating date range: {e}")

    # Adults: DIRECTLY SET TO 2 (as requested by user)
    # This ensures hotel search always uses 2 adults to avoid "NO RATE FOR REQUESTED OCCUPANCY" errors
    adults = 2
    logger.info(f"Hotel match adults set to 2 (fixed value)")

    must_have = options.get("must_have") or []
    nice_to_have = options.get("nice_to_have") or []
    
    # Extract additional requirements from SOW analysis
    if sow_analysis and not must_have:
        # Extract must-have requirements from SOW
        function_space = sow_analysis.get("FunctionSpaceRequirements", {})
        av_reqs = sow_analysis.get("AVRequirements", {})
        if function_space or av_reqs:
            must_have.append("Meeting space available")
            must_have.append("AV equipment support")

    return {
        "city_code": city_code.upper(),
        "city_name": city_name,
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults,
        "must_have": must_have,
        "nice_to_have": nice_to_have,
        "sow_analysis_used": bool(sow_analysis),  # Flag to indicate SOW analysis was used
        "document_analysis_used": bool(document_analysis),  # Flag to indicate document analysis was used
    }


def _derive_date(value: Optional[datetime], fallback_days: int) -> Optional[str]:
    if value:
        return value.date().isoformat()
    return (datetime.utcnow().date() + timedelta(days=fallback_days)).isoformat()


def _safe_iso_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None


def build_decision_cache_context(
    opportunity: Opportunity,
    requirements: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a decision-cache friendly context so cache signatures stay consistent between lookup/save.
    """
    options = options or {}
    check_in = requirements.get("check_in")
    check_out = requirements.get("check_out")
    nights = None
    start_dt = _safe_iso_date(check_in)
    end_dt = _safe_iso_date(check_out)
    if start_dt and end_dt:
        delta = (end_dt - start_dt).days
        nights = delta if delta >= 0 else None

    date_range = None
    if check_in and check_out:
        date_range = f"{check_in} to {check_out}"

    return {
        "notice_id": opportunity.notice_id,
        "city": requirements.get("city_name"),
        "state": options.get("state") or (opportunity.cached_data or {}).get("state"),
        "country": options.get("country") or "USA",
        "location": requirements.get("city_name") or opportunity.place_of_performance,
        "participants": requirements.get("adults"),
        "nights": nights,
        "date_range": date_range,
        "naics_code": opportunity.naics_code,
        "budget_total": options.get("budget_total") or (opportunity.cached_data or {}).get("estimated_value"),
        "event_requirements": {
            "must_have": requirements.get("must_have"),
            "nice_to_have": requirements.get("nice_to_have"),
        },
    }

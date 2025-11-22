"""
Thin wrapper around the Amadeus hotel search API.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from amadeus import Client, ResponseError

from ..config import settings

logger = logging.getLogger(__name__)


def _build_client() -> Optional[Client]:
    if not settings.amadeus_api_key or not settings.amadeus_api_secret:
        logger.warning("Amadeus API credentials are missing; hotel search disabled.")
        return None
    # Amadeus SDK expects "production" or "test" as hostname, not full URLs
    hostname = "production" if settings.amadeus_env.lower() == "production" else "test"
    try:
        return Client(
            client_id=settings.amadeus_api_key,
            client_secret=settings.amadeus_api_secret,
            hostname=hostname,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Failed to initialize Amadeus client: %s", exc)
        return None


_CLIENT = _build_client()


def search_hotels_by_city_code(
    city_code: str,
    check_in: str,
    check_out: str,
    adults: int = 1,
    max_results: int = 10,  # Increased from 5 to 10
) -> List[Dict[str, Any]]:
    """
    Fetch hotel offers and flatten structure for Agent compatibility.
    
    Returns formatted offers with 'name' at root level for easy access.
    """
    if not _CLIENT:
        return []
    try:
        # Step 1: Get hotel list by city code
        logger.info(f"Fetching hotel list for city code: {city_code}")
        try:
            hotel_list_response = _CLIENT.reference_data.locations.hotels.by_city.get(cityCode=city_code.upper())
        except AttributeError:
            # Fallback: try alternative API endpoint
            logger.warning("hotels.by_city not available, trying alternative method")
            # Use hotel list search instead
            hotel_list_response = _CLIENT.reference_data.locations.hotels.get(cityCode=city_code.upper())
        
        if not hotel_list_response.data or len(hotel_list_response.data) == 0:
            logger.warning(f"No hotels found for city code: {city_code}")
            return []
        
        # Extract hotel IDs (limit to first 20 to avoid too many requests)
        hotel_ids = [hotel.get('hotelId') for hotel in hotel_list_response.data[:20] if hotel.get('hotelId')]
        
        if not hotel_ids:
            logger.warning(f"No hotel IDs found in response for city code: {city_code}")
            return []
        
        logger.info(f"Found {len(hotel_ids)} hotels, fetching offers for first {min(len(hotel_ids), 10)}")
        
        # Step 2: Get offers for these hotels
        # Amadeus Hotel Offers Search requires hotelIds (not cityCode)
        offers_params = {
            'hotelIds': ','.join(hotel_ids[:10]),  # Limit to 10 hotels to avoid API limits
            'checkInDate': check_in,
            'checkOutDate': check_out,
            'adults': adults,
            'roomQuantity': adults,  # CRITICAL: roomQuantity = adults to avoid "NO RATE FOR REQUESTED OCCUPANCY" errors
            'bestRateOnly': True
        }
            
        offers_response = _CLIENT.shopping.hotel_offers_search.get(**offers_params)
        
        # --- CRITICAL FIX: DATA MAPPING ---
        # Flatten nested structure for Agent compatibility
        formatted_offers = []
        if offers_response.data:
            for hotel_data in offers_response.data:
                hotel_info = hotel_data.get('hotel', {})
                hotel_offers = hotel_data.get('offers', [])
                
                # Take first offer if available
                offer_data = hotel_offers[0] if hotel_offers else {}
                price_data = offer_data.get('price', {}) if offer_data else {}
                
                # Extract hotel name - CRITICAL: Must be at root level
                hotel_name = hotel_info.get('name', 'Unknown Hotel')
                
                # Flatten structure for Agent
                formatted_hotel = {
                    "name": hotel_name,  # <-- Root level name (CRITICAL for Agent)
                    "hotelId": hotel_info.get('hotelId'),
                    "latitude": hotel_info.get('latitude'),
                    "longitude": hotel_info.get('longitude'),
                    "cityCode": hotel_info.get('cityCode', city_code),
                    "rating": hotel_info.get('rating'),
                    "price": {
                        "total": price_data.get('total'),
                        "currency": price_data.get('currency'),
                        "base": price_data.get('base'),
                    },
                    "description": hotel_info.get('description', {}).get('text', '') if isinstance(hotel_info.get('description'), dict) else '',
                    "amenities": hotel_info.get('amenities', []),
                    # Keep nested structure for backward compatibility
                    "hotel": hotel_info,
                    "offer": offer_data,
                    # Keep raw data subset for reference
                    "raw_data_subset": {
                        "hotel": hotel_info,
                        "price": price_data
                    }
                }
                formatted_offers.append(formatted_hotel)
        
        # Sort by price if available and return top results
        if formatted_offers:
            try:
                formatted_offers.sort(key=lambda x: float(x.get('price', {}).get('total', '999999') or '999999'))
            except (ValueError, TypeError):
                pass  # If sorting fails, return unsorted
        
        return formatted_offers[:max_results]
        
    except ResponseError as exc:
        logger.error(f"Amadeus API error: {exc.code} - {exc.description}")
        if hasattr(exc, 'response') and exc.response:
            logger.error(f"Response body: {exc.response.body}")
        # Log request parameters for debugging
        logger.error(f"Request params: city_code={city_code}, check_in={check_in}, check_out={check_out}, adults={adults}")
        return []
    except Exception as exc:
        logger.error("Amadeus hotel search error: %s", exc, exc_info=True)
        # Log more details about the error
        if hasattr(exc, 'response'):
            logger.error(f"Error response: {exc.response}")
        if hasattr(exc, 'description'):
            logger.error(f"Error description: {exc.description}")
        if hasattr(exc, 'code'):
            logger.error(f"Error code: {exc.code}")
        # Log request parameters for debugging
        logger.error(f"Request params: city_code={city_code}, check_in={check_in}, check_out={check_out}, adults={adults}")
        return []


def lookup_city_code(city_name: str) -> Optional[str]:
    """
    Resolve a free-form city name (e.g. 'Houston') to an IATA city code (e.g. 'HOU').
    """
    if not _CLIENT:
        return None
    try:
        resp = _CLIENT.reference_data.locations.get(
            keyword=city_name,
            subType="CITY",
        )
        if not resp.data:
            return None
        return resp.data[0].get("iataCode")
    except ResponseError as exc:
        logger.warning("Amadeus city lookup failed for %s: %s", city_name, exc)
        return None


def normalize_date(value: Optional[str], fallback_days: int = 0) -> Optional[str]:
    """
    Ensure date strings are ISO format (YYYY-MM-DD). If value is None,
    returns today's date + fallback_days.
    """
    if value:
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            pass
    base_date = datetime.utcnow().date()
    if fallback_days:
        base_date = base_date + timedelta(days=fallback_days)
    return base_date.isoformat()


def is_amadeus_configured() -> bool:
    """Return True if API credentials are configured."""
    return bool(settings.amadeus_api_key and settings.amadeus_api_secret)


def amadeus_health_check(test_city: str = "Washington", nights: int = 2) -> Dict[str, Any]:
    """
    Perform a lightweight health check against Amadeus API.
    Returns diagnostic information without raising.
    """
    status = {
        "configured": is_amadeus_configured(),
        "environment": settings.amadeus_env,
        "client_initialized": _CLIENT is not None,
        "status": "disabled",
        "city_code": None,
        "offers_found": 0,
    }
    if not _CLIENT:
        status["status"] = "disabled"
        return status
    
    city_code = lookup_city_code(test_city)
    status["city_code"] = city_code
    if not city_code:
        status["status"] = "city_lookup_failed"
        return status
    
    check_in = (datetime.utcnow().date() + timedelta(days=30)).isoformat()
    check_out = (datetime.utcnow().date() + timedelta(days=30 + max(nights, 1))).isoformat()
    offers = search_hotels_by_city_code(city_code, check_in, check_out, adults=1, max_results=1)
    status["offers_found"] = len(offers)
    status["status"] = "ok" if offers else "no_offers"
    return status

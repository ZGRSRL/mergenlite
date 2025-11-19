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
    max_results: int = 5,
) -> List[Dict[str, Any]]:
    """
    Fetch hotel offers for given city code + stay window.
    Dates must be ISO strings (YYYY-MM-DD).
    """
    if not _CLIENT:
        return []
    try:
        # Amadeus Hotel Search API - SDK has hotel_offers_search
        # Note: Some parameters may be optional or have different names
        params = {
            'cityCode': city_code.upper(),
        }
        # Add optional parameters only if provided
        if check_in:
            params['checkInDate'] = check_in
        if check_out:
            params['checkOutDate'] = check_out
        if adults:
            params['adults'] = adults
            
        response = _CLIENT.shopping.hotel_offers_search.get(**params)
        return response.data[:max_results] if hasattr(response, 'data') and response.data else []
    except (ResponseError, Exception) as exc:
        logger.error("Amadeus hotel search error: %s", exc, exc_info=True)
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

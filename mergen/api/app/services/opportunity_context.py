"""
Helpers to derive structured hotel search requirements from an Opportunity.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from ..models import Opportunity
from .amadeus_client import lookup_city_code


def _extract_city_from_title(title: Optional[str]) -> Optional[str]:
    if not title:
        return None
    if "-" in title:
        tail = title.split("-")[-1].strip()
        return tail.split("(")[0].strip()
    return title.strip()


def build_hotel_match_requirements(opportunity: Opportunity, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Build a minimal requirement payload for the HotelMatcher agent.
    Priority:
      - values provided in options
      - values stored on opportunity (cached_data/place_of_performance/etc)
      - basic fallbacks
    """
    options = options or {}
    cached = opportunity.cached_data or {}

    city_code = options.get("city_code") or cached.get("cityCode")
    city_name = (
        options.get("city_name")
        or cached.get("placeOfPerformance")
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
        raise ValueError(f"City code could not be determined for '{city_name}'; provide options.city_code.")

    check_in = options.get("check_in") or _derive_date(opportunity.response_deadline, fallback_days=30)
    check_out = options.get("check_out") or _derive_date(opportunity.response_deadline, fallback_days=33)

    if not check_in or not check_out:
        raise ValueError("Check-in/out dates are required; provide options.check_in/check_out.")

    adults = int(options.get("adults") or cached.get("participants_target") or 10)

    must_have = options.get("must_have") or []
    nice_to_have = options.get("nice_to_have") or []

    return {
        "city_code": city_code.upper(),
        "city_name": city_name,
        "check_in": check_in,
        "check_out": check_out,
        "adults": adults,
        "must_have": must_have,
        "nice_to_have": nice_to_have,
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

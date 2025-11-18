"""
Helpers for building decision cache signatures, lookups, and persistence.
"""
import hashlib
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from ..models import Opportunity, AIAnalysisResult, DecisionCache
from .history_service import upsert_decision_cache, get_decision_cache

logger = logging.getLogger(__name__)


def _safe_number(value: Optional[Any]) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^0-9.]", "", value)
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _bucketize(value: Optional[float], boundaries: Tuple[Tuple[int, str], ...], default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    for upper, label in boundaries:
        if value <= upper:
            return label
    return f">{boundaries[-1][0]}"


def _parse_date(date_str: str) -> Optional[datetime]:
    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%b %d, %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


def _calculate_nights(context: Dict[str, Any], event_req: Optional[Dict[str, Any]]) -> Optional[int]:
    if context.get("nights"):
        return context["nights"]
    date_range = (
        context.get("date_range")
        or (event_req or {}).get("date_range")
        or (event_req or {}).get("schedule")
    )
    if not date_range or "to" not in date_range:
        return None
    start_str, end_str = [part.strip() for part in date_range.split("to", 1)]
    start = _parse_date(start_str)
    end = _parse_date(end_str)
    if not start or not end:
        return None
    diff = (end - start).days
    return diff if diff >= 0 else None


def _split_location(location: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not location:
        return None, None
    parts = [part.strip() for part in re.split(r"[,/]", location) if part.strip()]
    if not parts:
        return None, None
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


def _load_event_requirements(db: Session, opportunity_id: int) -> Optional[Dict[str, Any]]:
    result = (
        db.query(AIAnalysisResult)
        .filter(AIAnalysisResult.opportunity_id == opportunity_id)
        .order_by(AIAnalysisResult.created_at.desc())
        .first()
    )
    if not result or not result.result_json:
        return None
    return result.result_json.get("event_requirements")


def _extract_from_opportunity(opportunity: Opportunity) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if opportunity.cached_data:
        data.update(opportunity.cached_data)
    if opportunity.raw_data:
        data.setdefault("raw", opportunity.raw_data)
    return data


def build_signature(
    *,
    opportunity: Optional[Opportunity],
    context: Optional[Dict[str, Any]],
    event_requirements: Optional[Dict[str, Any]],
) -> Tuple[str, Dict[str, str]]:
    ctx = {k: v for k, v in (context or {}).items() if v is not None}
    city = ctx.get("city")
    state = ctx.get("state")
    country = ctx.get("country") or "USA"
    location = ctx.get("location") or (event_requirements or {}).get("location")
    if not city and location:
        city, inferred_state = _split_location(location)
        state = state or inferred_state
    if not city and opportunity:
        cached = _extract_from_opportunity(opportunity)
        cached_loc = cached.get("location") or cached.get("opportunity_info", {}).get("place_of_performance")
        if isinstance(cached_loc, str):
            city, inferred_state = _split_location(cached_loc)
            state = state or inferred_state

    participants = (
        ctx.get("participants")
        or (event_requirements or {}).get("participants_target")
        or (event_requirements or {}).get("participants_min")
    )
    budget_total = ctx.get("budget_total") or _safe_number(ctx.get("estimated_value"))
    if budget_total is None and opportunity:
        cached = _extract_from_opportunity(opportunity)
        budget_total = _safe_number(
            (cached.get("commercial_terms") or {}).get("estimated_value")
            or cached.get("estimated_value")
        )

    nights = _calculate_nights(ctx, event_requirements)
    naics = ctx.get("naics_code") or (opportunity.naics_code if opportunity else None) or "UNKNOWN"
    location_type = ctx.get("location_type") or (event_requirements or {}).get("location_type") or "general"

    signature = {
        "city": (city or "UNKNOWN").upper(),
        "state": (state or "UNKNOWN").upper(),
        "country": country.upper(),
        "nights": _bucketize(
            nights,
            (
                (2, "1-2"),
                (4, "3-4"),
                (7, "5-7"),
                (14, "8-14"),
            ),
        ),
        "participants": _bucketize(
            participants,
            (
                (25, "1-25"),
                (50, "26-50"),
                (100, "51-100"),
                (250, "101-250"),
                (500, "251-500"),
            ),
        ),
        "budget": _bucketize(
            budget_total,
            (
                (5000, "<=5k"),
                (20000, "5k-20k"),
                (50000, "20k-50k"),
                (100000, "50k-100k"),
            ),
        ),
        "naics": str(naics).upper(),
        "location_type": str(location_type).lower(),
    }
    key_basis = "|".join(f"{k}:{signature[k]}" for k in sorted(signature.keys()))
    key_hash = hashlib.md5(key_basis.encode("utf-8")).hexdigest()
    return key_hash, signature


def lookup_decision_cache(
    db: Session,
    *,
    opportunity: Optional[Opportunity],
    context: Optional[Dict[str, Any]] = None,
    notice_id: Optional[str] = None,
) -> Tuple[str, Dict[str, str], Optional[DecisionCache]]:
    event_req = None
    if context and context.get("event_requirements"):
        event_req = context.get("event_requirements")
    elif opportunity:
        event_req = _load_event_requirements(db, opportunity.id)

    key_hash, signature = build_signature(
        opportunity=opportunity,
        context=context,
        event_requirements=event_req,
    )

    entry = get_decision_cache(db, key_hash)
    if entry:
        return key_hash, signature, entry

    if notice_id:
        candidate = (
            db.query(DecisionCache)
            .order_by(DecisionCache.created_at.desc())
            .limit(50)
            .all()
        )
        for item in candidate:
            meta = item.extra_metadata or {}
            notice_ids = meta.get("notice_ids") or []
            if notice_id in notice_ids:
                return key_hash, signature, item

    return key_hash, signature, None


def persist_decision_cache(
    db: Session,
    *,
    opportunity: Optional[Opportunity],
    context: Optional[Dict[str, Any]],
    recommended_hotels: Optional[Any],
    pattern_desc: Optional[str],
    notice_id: Optional[str] = None,
    key_hash: str,
    signature: Dict[str, str],
) -> DecisionCache:
    existing = get_decision_cache(db, key_hash)
    metadata = {
        "signature": signature,
        "context": context or {},
        "last_saved_at": datetime.utcnow().isoformat(),
    }
    if existing and isinstance(existing.extra_metadata, dict):
        metadata = {**existing.extra_metadata, **metadata}
        if "signature" in existing.extra_metadata:
            metadata["signature"] = existing.extra_metadata["signature"]
        if "context" in existing.extra_metadata and not context:
            metadata["context"] = existing.extra_metadata["context"]
    if notice_id:
        metadata.setdefault("notice_ids", [])
        if notice_id not in metadata["notice_ids"]:
            metadata["notice_ids"].append(notice_id)
    if opportunity:
        metadata.setdefault("opportunity_ids", [])
        if opportunity.id not in metadata["opportunity_ids"]:
            metadata["opportunity_ids"].append(opportunity.id)

    entry = upsert_decision_cache(
        db,
        key_hash=key_hash,
        pattern_desc=pattern_desc,
        recommended_hotels=recommended_hotels,
        metadata=metadata,
    )
    return entry

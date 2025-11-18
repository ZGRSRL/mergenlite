"""
Utility client for talking to the FastAPI decision cache endpoints.
"""
import logging
import os
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


def build_decision_context(
    event_requirements: Optional[Dict[str, Any]],
    opportunity_info: Optional[Dict[str, Any]],
    *,
    notice_id: Optional[str] = None,
) -> Dict[str, Any]:
    ctx: Dict[str, Any] = {}
    event_req = event_requirements or {}
    opp_info = opportunity_info or {}

    location = event_req.get("location") or opp_info.get("place_of_performance")
    if location:
        ctx["location"] = location
    if opp_info.get("city"):
        ctx["city"] = opp_info["city"]
    if opp_info.get("state"):
        ctx["state"] = opp_info["state"]
    if event_req.get("participants_target") or event_req.get("participants_min"):
        ctx["participants"] = event_req.get("participants_target") or event_req.get("participants_min")
    if event_req.get("date_range"):
        ctx["date_range"] = event_req["date_range"]
    if event_req.get("nights"):
        ctx["nights"] = event_req["nights"]
    if event_req.get("budget"):
        ctx["budget_total"] = event_req["budget"]
    if notice_id or opp_info.get("notice_id"):
        ctx["notice_id"] = notice_id or opp_info.get("notice_id")
    if opp_info.get("naics"):
        ctx["naics_code"] = opp_info.get("naics")
    return ctx


class DecisionCacheClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv("MERGEN_API_URL") or os.getenv("BACKEND_URL")
        self.default_opportunity_id = int(os.getenv("MERGEN_OPPORTUNITY_ID", "0") or "0")
        self.session: Optional[requests.Session] = None
        if self.base_url:
            self.session = requests.Session()
            logger.debug("DecisionCacheClient enabled for %s", self.base_url)
        else:
            logger.debug("DecisionCacheClient disabled (MERGEN_API_URL missing)")

    def enabled(self) -> bool:
        return self.session is not None

    def lookup(
        self,
        context: Dict[str, Any],
        *,
        opportunity_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self.session:
            return None
        opp_id = opportunity_id if opportunity_id is not None else self.default_opportunity_id
        url = f"{self.base_url}/api/opportunities/{opp_id or 0}/decision-cache/lookup"
        try:
            response = self.session.post(url, json=context, timeout=15)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.warning("Decision cache lookup failed: %s", exc)
            return None

    def save(
        self,
        context: Dict[str, Any],
        recommended_hotels: Any,
        *,
        pattern_desc: Optional[str] = None,
        opportunity_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        if not self.session:
            return None
        payload = dict(context)
        payload["recommended_hotels"] = recommended_hotels
        payload["pattern_desc"] = pattern_desc
        opp_id = opportunity_id if opportunity_id is not None else self.default_opportunity_id
        url = f"{self.base_url}/api/opportunities/{opp_id or 0}/decision-cache/save"
        try:
            response = self.session.post(url, json=payload, timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            logger.warning("Decision cache save failed: %s", exc)
            return None

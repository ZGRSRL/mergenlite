from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..db import get_db
from ..models import Opportunity
from sqlalchemy.orm import Session
from datetime import datetime
from ..services.redis_client import cache_get_json, cache_set_json, token_bucket_allow
from ..services.circuit_breaker import CircuitBreaker

SAMIntegration = None
SAM_AVAILABLE = False
try:
    from ....sam_integration import SAMIntegration  # type: ignore
    SAM_AVAILABLE = True
except Exception:  # pragma: no cover
    import sys, os
    ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
    if ROOT not in sys.path:
        sys.path.append(ROOT)
    try:
        from sam_integration import SAMIntegration  # type: ignore
        SAM_AVAILABLE = True
    except Exception:
        SAMIntegration = None
        SAM_AVAILABLE = False

router = APIRouter(prefix="/api/proxy/opportunities", tags=["proxy"])


def _cache_key(prefix: str, params: Dict[str, Any]) -> str:
    items = sorted((k, str(v)) for k, v in params.items())
    joined = "&".join(f"{k}={v}" for k, v in items)
    return f"{prefix}:{joined}"


def _parse_dt(v: Any):
    if not v:
        return None
    if isinstance(v, (int, float)):
        try:
            return datetime.fromtimestamp(v)
        except Exception:
            return None
    s = str(v)
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def _upsert_opportunities(db: Session, items: List[Dict[str, Any]]) -> int:
    saved = 0
    for it in items:
        try:
            notice_id = it.get('noticeId') or it.get('solicitationNumber') or ''
            if not notice_id:
                continue
            opp = db.query(Opportunity).filter(Opportunity.notice_id == notice_id).first()
            if not opp:
                opp = Opportunity(notice_id=notice_id)
                db.add(opp)
            opp.opportunity_id = it.get('opportunityId')
            opp.title = it.get('title')
            opp.naics_code = it.get('naicsCode')
            opp.organization = it.get('fullParentPathName') or it.get('organization')
            opp.posted_date = _parse_dt(it.get('postedDate'))
            opp.response_deadline = _parse_dt(it.get('responseDeadLine'))
            opp.source = it.get('source') or 'sam_live'
            opp.raw_json = it
            saved += 1
        except Exception:
            continue
    try:
        db.commit()
    except Exception:
        db.rollback()
    return saved


@router.get("/search")
def proxy_search(
    naics: str = Query("721110"),
    days_back: int = Query(30, ge=1, le=365),
    limit: int = Query(100, ge=1, le=1000),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    params = {
        "naics": naics,
        "days_back": days_back,
        "limit": limit,
        "keyword": keyword or "",
    }
    ck = _cache_key("search", params)

    cached = cache_get_json(ck)
    if cached is not None:
        return JSONResponse(content=cached, headers={"X-Cache": "HIT", "X-Source": "cache"})

    # Rate limit & circuit breaker
    if not token_bucket_allow("sam_search", rate_per_sec=1.0, burst=3):
        raise HTTPException(status_code=429, detail="Rate limited. Please retry.")

    if not SAM_AVAILABLE or SAMIntegration is None:
        raise HTTPException(status_code=503, detail="SAM integration is not available in this deployment.")

    cb = CircuitBreaker("sam_search")
    if not cb.allow():
        raise HTTPException(status_code=503, detail="Service temporarily unavailable (circuit open)")

    sam = SAMIntegration()
    try:
        results = sam.fetch_opportunities(
            keywords=keyword,
            naics_codes=[naics],
            days_back=days_back,
            limit=limit,
            page_size=1000,
        )
        # Server-side hard filter by NAICS to avoid mixed results from upstream
        try:
            results = [r for r in results if str(r.get('naicsCode', '')).strip() == str(naics).strip()]
        except Exception:
            pass
        cb.record_success()
    except Exception:
        cb.record_failure()
        raise

    # DB'ye yaz (NAICS ve tarih aralığı ile gelen sonuçlar)
    try:
        saved = _upsert_opportunities(db, results)
    except Exception:
        saved = 0

    payload = {"total": len(results), "results": results, "saved": saved}
    cache_set_json(ck, payload, ttl_seconds=1800)
    return JSONResponse(content=payload, headers={"X-Cache": "MISS", "X-Source": "sam_live"})


@router.get("/noticedesc")
def proxy_noticedesc(id: str = Query(..., description="Notice ID, Opportunity ID veya SAM URL")):
    ck = _cache_key("noticedesc", {"id": id})
    cached = cache_get_json(ck)
    if cached is not None:
        return JSONResponse(content=cached, headers={"X-Cache": "HIT", "X-Source": "cache"})

    if not token_bucket_allow("sam_desc", rate_per_sec=1.0, burst=3):
        raise HTTPException(status_code=429, detail="Rate limited. Please retry.")

    if not SAM_AVAILABLE or SAMIntegration is None:
        raise HTTPException(status_code=503, detail="SAM integration is not available in this deployment.")

    cb = CircuitBreaker("sam_desc")
    if not cb.allow():
        raise HTTPException(status_code=503, detail="Service temporarily unavailable (circuit open)")

    sam = SAMIntegration()
    try:
        # Önce akıllı ID araması (URL/oppId/noticeId)
        items = sam.search_by_any_id(id)
        if items:
            payload = {"success": True, "items": items}
        else:
            # Tek ilan detay (noticedesc)
            details = sam.get_opportunity_details(id)
            payload = details
        cb.record_success()
    except Exception:
        cb.record_failure()
        raise

    cache_set_json(ck, payload, ttl_seconds=3600)
    return JSONResponse(content=payload, headers={"X-Cache": "MISS", "X-Source": "sam_live"})

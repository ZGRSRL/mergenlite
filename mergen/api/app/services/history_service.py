"""
Utility helpers for opportunity history, decision cache, and training examples.
"""
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from ..models import (
    OpportunityHistory,
    TrainingExample,
    DecisionCache,
)


def record_opportunity_history(
    db: Session,
    *,
    opportunity_id: int,
    old_status: Optional[str],
    new_status: str,
    changed_by: str,
    change_source: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> OpportunityHistory:
    history = OpportunityHistory(
        opportunity_id=opportunity_id,
        old_status=old_status,
        new_status=new_status,
        changed_by=changed_by,
        change_source=change_source,
        meta=meta,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def add_training_example(
    db: Session,
    *,
    opportunity_id: Optional[int],
    example_type: str,
    input_data: Optional[Dict[str, Any]],
    output_data: Optional[Dict[str, Any]],
    outcome: Optional[str] = None,
    rating: Optional[int] = None,
) -> TrainingExample:
    example = TrainingExample(
        opportunity_id=opportunity_id,
        example_type=example_type,
        input_data=input_data,
        output_data=output_data,
        outcome=outcome,
        rating=rating,
    )
    db.add(example)
    db.commit()
    db.refresh(example)
    return example


def upsert_decision_cache(
    db: Session,
    *,
    key_hash: str,
    pattern_desc: Optional[str],
    recommended_hotels: Optional[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
) -> DecisionCache:
    cache = db.query(DecisionCache).filter(DecisionCache.key_hash == key_hash).first()
    if cache:
        cache.pattern_desc = pattern_desc
        cache.recommended_hotels = recommended_hotels
        cache.extra_metadata = metadata
        cache.created_at = datetime.utcnow()
    else:
        cache = DecisionCache(
            key_hash=key_hash,
            pattern_desc=pattern_desc,
            recommended_hotels=recommended_hotels,
            extra_metadata=metadata,
        )
        db.add(cache)
    db.commit()
    db.refresh(cache)
    return cache


def get_decision_cache(db: Session, key_hash: str) -> Optional[DecisionCache]:
    return db.query(DecisionCache).filter(DecisionCache.key_hash == key_hash).first()

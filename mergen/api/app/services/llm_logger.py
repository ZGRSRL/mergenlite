"""
LLM call wrapper that logs every request/response to the database.
"""
import time
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..models import LLMCall

logger = logging.getLogger(__name__)


class LLMClientWrapper:
    """
    Placeholder wrapper around an LLM client (OpenAI, etc.).
    Replace `self.client` calls with the actual provider.
    """

    def __init__(self, provider: str, client: Any):
        self.provider = provider
        self.client = client

    def chat_completion(self, model: str, messages: List[Dict[str, str]], **kwargs):
        t0 = time.time()
        response = self.client.chat.completions.create(model=model, messages=messages, **kwargs)
        latency = int((time.time() - t0) * 1000)
        tokens = response.usage or {}
        return response, latency, tokens.get("prompt_tokens"), tokens.get("completion_tokens"), tokens.get("total_tokens")


def log_llm_call(
    db: Session,
    provider: str,
    model: str,
    prompt: Optional[str],
    response_text: Optional[str],
    agent_run_id: Optional[int],
    agent_name: Optional[str],
    prompt_tokens: Optional[int],
    completion_tokens: Optional[int],
    total_tokens: Optional[int],
    latency_ms: Optional[int],
) -> LLMCall:
    call = LLMCall(
        provider=provider,
        model=model,
        prompt=prompt,
        response=response_text,
        agent_run_id=agent_run_id,
        agent_name=agent_name,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
    )
    db.add(call)
    db.commit()
    db.refresh(call)
    return call


def call_llm_with_logging(
    *,
    provider: str,
    model: str,
    messages: List[Dict[str, str]],
    agent_run_id: Optional[int] = None,
    agent_name: Optional[str] = None,
    client_wrapper: Optional[LLMClientWrapper] = None,
    **kwargs,
) -> Any:
    """
    Unified entry point for LLM calls with automatic DB logging.
    """
    if client_wrapper is None:
        raise ValueError("LLM client wrapper must be provided")

    prompt_text = "\n".join(f"{m['role']}: {m.get('content', '')}" for m in messages)

    response, latency, prompt_tokens, completion_tokens, total_tokens = client_wrapper.chat_completion(
        model=model,
        messages=messages,
        **kwargs,
    )

    response_text = getattr(response, "choices", [{}])[0].get("message", {}).get("content", "")

    db = SessionLocal()
    try:
        log_llm_call(
            db=db,
            provider=provider,
            model=model,
            prompt=prompt_text,
            response_text=response_text,
            agent_run_id=agent_run_id,
            agent_name=agent_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency,
        )
    finally:
        db.close()

    return response

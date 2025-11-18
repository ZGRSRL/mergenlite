"""
Helper utilities to ensure every LLM call goes through the FastAPI logging layer.
"""
import os
import logging
from typing import List, Dict, Any, Optional

try:
    import openai  # type: ignore

    OPENAI_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    openai = None  # type: ignore
    OPENAI_AVAILABLE = False

try:
    from mergen.api.app.services.llm_logger import LLMClientWrapper, call_llm_with_logging
except Exception as exc:  # pragma: no cover - defensive guard
    LLM_LOGGER_IMPORT_ERROR = exc
    LLM_LOGGER_AVAILABLE = False
else:
    LLM_LOGGER_IMPORT_ERROR = None
    LLM_LOGGER_AVAILABLE = True

logger = logging.getLogger(__name__)

_LLM_WRAPPER: Optional["LLMClientWrapper"] = None


class LLMNotAvailableError(RuntimeError):
    """Raised when no LLM client can be created."""


def _ensure_wrapper() -> "LLMClientWrapper":
    """
    Return a cached LLMClientWrapper instance.
    Raises LLMNotAvailableError if requirements are missing.
    """
    global _LLM_WRAPPER

    if not OPENAI_AVAILABLE:
        raise LLMNotAvailableError("openai package not installed")

    if not LLM_LOGGER_AVAILABLE:
        raise LLMNotAvailableError(f"llm_logger import failed: {LLM_LOGGER_IMPORT_ERROR}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMNotAvailableError("OPENAI_API_KEY is not set")

    model = os.getenv("OPENAI_MODEL")
    if not model:
        logger.debug("OPENAI_MODEL not set, falling back to gpt-4o-mini")

    openai.api_key = api_key

    if _LLM_WRAPPER is None:
        _LLM_WRAPPER = LLMClientWrapper(provider="openai", client=openai)

    return _LLM_WRAPPER


def llm_is_available() -> bool:
    """Public helper for modules that need to know if a real LLM call can be made."""
    if not OPENAI_AVAILABLE or not LLM_LOGGER_AVAILABLE:
        return False
    return bool(os.getenv("OPENAI_API_KEY"))


def call_logged_llm(
    *,
    messages: List[Dict[str, Any]],
    agent_name: str,
    agent_run_id: Optional[int] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs: Any,
) -> Any:
    """
    Unified LLM entry point for every agent.
    The raw provider response is returned for compatibility.
    """
    wrapper = _ensure_wrapper()
    payload: Dict[str, Any] = {}
    if temperature is not None:
        payload["temperature"] = temperature
    payload.update(kwargs)

    return call_llm_with_logging(
        provider="openai",
        model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
        agent_run_id=agent_run_id,
        agent_name=agent_name,
        client_wrapper=wrapper,
        **payload,
    )


def extract_message_text(response: Any) -> str:
    """Utility to read the assistant text from an OpenAI chat completion response."""
    try:
        return response.choices[0].message.get("content") or ""
    except Exception:  # pragma: no cover - defensive
        return ""


"""
MergenLite — Telegram Notification Service
===========================================
Lightweight error tracking and monitoring via Telegram.

Features:
  - Send alerts on critical errors (5xx, DB failures, pipeline crashes)
  - Configurable severity levels (INFO, WARNING, ERROR, CRITICAL)
  - Rate limiting to prevent spam
  - Rich formatting with context data
  - Async/non-blocking notifications

Environment Variables:
  TELEGRAM_BOT_TOKEN - Bot API token from @BotFather
  TELEGRAM_CHAT_ID - Your chat ID
  TELEGRAM_ENABLED - Enable/disable notifications (default: false)
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from collections import defaultdict

import httpx

from ..config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate Limiting (prevent spam)
# ---------------------------------------------------------------------------
_last_alert_time: Dict[str, float] = defaultdict(float)
_COOLDOWN_SECONDS = 60  # Same alert type only once per minute


# ---------------------------------------------------------------------------
# Core Function
# ---------------------------------------------------------------------------
async def send_telegram_alert(
    severity: str,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    force: bool = False,
) -> bool:
    """
    Send alert to Telegram.

    Args:
        severity: INFO, WARNING, ERROR, CRITICAL
        message: Short description
        context: Additional metadata (dict)
        force: Skip rate limiting

    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.telegram_enabled:
        logger.debug("Telegram notifications disabled")
        return False

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("Telegram credentials not configured")
        return False

    # Rate limiting
    alert_key = f"{severity}:{message[:50]}"
    if not force:
        last_time = _last_alert_time[alert_key]
        if time.time() - last_time < _COOLDOWN_SECONDS:
            logger.debug(f"Alert rate-limited: {alert_key}")
            return False
        _last_alert_time[alert_key] = time.time()

    # Format message
    emoji = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "🚨",
        "CRITICAL": "💥",
    }.get(severity, "📢")

    text = f"{emoji} *{severity}*\n\n{message}"

    if context:
        text += "\n\n*Details:*"
        for key, value in context.items():
            # Truncate long values
            val_str = str(value)
            if len(val_str) > 100:
                val_str = val_str[:97] + "..."
            text += f"\n• `{key}`: {val_str}"

    text += f"\n\n_MergenLite v2.0 • {time.strftime('%Y-%m-%d %H:%M:%S')}_"

    # Send to Telegram
    try:
        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": settings.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()

        logger.info(f"Telegram alert sent: {severity} - {message}")
        return True

    except Exception as exc:
        logger.error(f"Failed to send Telegram alert: {exc}")
        return False


# ---------------------------------------------------------------------------
# Convenience Wrappers
# ---------------------------------------------------------------------------
async def notify_error(message: str, context: Optional[Dict[str, Any]] = None):
    """Send ERROR level notification."""
    await send_telegram_alert("ERROR", message, context)


async def notify_critical(message: str, context: Optional[Dict[str, Any]] = None):
    """Send CRITICAL level notification (bypasses rate limit)."""
    await send_telegram_alert("CRITICAL", message, context, force=True)


async def notify_warning(message: str, context: Optional[Dict[str, Any]] = None):
    """Send WARNING level notification."""
    await send_telegram_alert("WARNING", message, context)


async def notify_info(message: str, context: Optional[Dict[str, Any]] = None):
    """Send INFO level notification."""
    await send_telegram_alert("INFO", message, context)


# ---------------------------------------------------------------------------
# Background task runner (for sync contexts)
# ---------------------------------------------------------------------------
def send_alert_background(severity: str, message: str, context: Optional[Dict[str, Any]] = None):
    """
    Fire-and-forget alert sender for synchronous code.
    Creates a new event loop to run the async alert.
    """
    try:
        asyncio.create_task(send_telegram_alert(severity, message, context))
    except RuntimeError:
        # No event loop — create one
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_telegram_alert(severity, message, context))
            loop.close()
        except Exception as exc:
            logger.error(f"Background alert failed: {exc}")

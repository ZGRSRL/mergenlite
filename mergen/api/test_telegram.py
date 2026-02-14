"""
Telegram Notification Test
===========================
Tests the full notification pipeline.

Run this AFTER you've set up your Telegram bot and updated .env with:
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHAT_ID=...
  TELEGRAM_ENABLED=true
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.notifications import (
    send_telegram_alert,
    notify_info,
    notify_warning,
    notify_error,
    notify_critical,
)
from app.config import settings


async def main():
    print("=== Telegram Notification Test ===\n")

    # Check config
    print(f"Telegram enabled: {settings.telegram_enabled}")
    print(f"Bot token configured: {'Yes' if settings.telegram_bot_token else 'No'}")
    print(f"Chat ID configured: {'Yes' if settings.telegram_chat_id else 'No'}")
    print()

    if not settings.telegram_enabled:
        print("❌ Telegram notifications disabled in .env")
        print("   Set TELEGRAM_ENABLED=true and configure bot credentials.")
        return

    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        print("❌ Missing Telegram credentials")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
        return

    # Run tests
    tests = [
        ("INFO", notify_info, "Test INFO notification — monitoring active ✅", {}),
        (
            "WARNING",
            notify_warning,
            "Test WARNING — pipeline processing slow",
            {"duration": "45s", "threshold": "30s"},
        ),
        (
            "ERROR",
            notify_error,
            "Test ERROR — API rate limit exceeded",
            {"api": "SAM.gov", "retry_after": "60s"},
        ),
        (
            "CRITICAL",
            notify_critical,
            "Test CRITICAL — database connection lost",
            {"error": "connection timeout", "host": "localhost:5432"},
        ),
    ]

    for i, (severity, func, message, context) in enumerate(tests, 1):
        print(f"\n[{i}/4] Sending {severity} notification...")
        try:
            result = await func(message, context)
            if result:
                print(f"  ✅ Sent successfully")
            else:
                print(f"  ⚠️ Skipped (disabled or rate-limited)")
        except Exception as exc:
            print(f"  ❌ Failed: {exc}")

        # Delay between messages
        if i < len(tests):
            await asyncio.sleep(2)

    print("\n=== Test Complete ===")
    print("Check your Telegram for 4 messages!")


if __name__ == "__main__":
    asyncio.run(main())

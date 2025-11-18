import json
import time
from typing import Any, Optional

from ..config import settings

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # Fallback için


class _InMemoryStore:
    def __init__(self):
        self._kv = {}

    def setex(self, key: str, ttl: int, value: str):
        self._kv[key] = (time.time() + ttl, value)

    def get(self, key: str) -> Optional[str]:
        v = self._kv.get(key)
        if not v:
            return None
        exp, val = v
        if time.time() > exp:
            self._kv.pop(key, None)
            return None
        return val

    def incr(self, key: str, amount: int = 1) -> int:
        exp, val = self._kv.get(key, (time.time() + 60, "0"))
        new_val = str(int(val) + amount)
        self._kv[key] = (exp, new_val)
        return int(new_val)

    def expire(self, key: str, ttl: int):
        v = self._kv.get(key)
        if v:
            _, val = v
            self._kv[key] = (time.time() + ttl, val)


def _make_client():
    if redis is None:
        return _InMemoryStore()
    try:
        client = redis.from_url(settings.redis_url, decode_responses=True)
        # Ping to verify
        client.ping()
        return client
    except Exception:
        return _InMemoryStore()


_client = _make_client()


def cache_get_json(key: str) -> Optional[Any]:
    try:
        raw = _client.get(key)
        if not raw:
            return None
        return json.loads(raw)
    except Exception:
        return None


def cache_set_json(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    try:
        _client.setex(key, ttl_seconds, json.dumps(value))
    except Exception:
        pass


def token_bucket_allow(bucket: str, rate_per_sec: float = 1.0, burst: int = 3) -> bool:
    """Basit token bucket: saniyede rate_per_sec, birikmiş en fazla burst."""
    now = int(time.time())
    counter_key = f"tb:{bucket}:{now}"
    try:
        count = _client.incr(counter_key, 1)
        _client.expire(counter_key, 1)
        if count <= max(1, int(burst)):
            return True
        return False
    except Exception:
        return True


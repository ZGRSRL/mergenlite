import time
from typing import Optional

from .redis_client import _client


def _now() -> int:
    return int(time.time())


class CircuitBreaker:
    """Basit circuit breaker (Redis tabanlı).

    CLOSED -> başarısızlık say, eşik aşılırsa OPEN
    OPEN -> cooldown süresi dolana kadar çağrıları blokla
    HALF_OPEN -> bir denemeye izin ver, başarılıysa CLOSED, değilse OPEN
    """

    def __init__(self, name: str, failure_threshold: int = 5, cooldown_sec: int = 60):
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_sec = cooldown_sec

    @property
    def _state_key(self) -> str:
        return f"cb:{self.name}:state"

    @property
    def _fail_key(self) -> str:
        return f"cb:{self.name}:failures"

    @property
    def _until_key(self) -> str:
        return f"cb:{self.name}:until"

    def _get(self, key: str) -> Optional[str]:
        try:
            return _client.get(key)
        except Exception:
            return None

    def _setex(self, key: str, ttl: int, val: str) -> None:
        try:
            _client.setex(key, ttl, val)
        except Exception:
            pass

    def allow(self) -> bool:
        state = self._get(self._state_key) or "CLOSED"
        if state == "OPEN":
            until = int(self._get(self._until_key) or "0")
            if _now() >= until:
                # HALF_OPEN
                self._setex(self._state_key, self.cooldown_sec, "HALF_OPEN")
                return True
            return False
        return True

    def record_success(self) -> None:
        self._setex(self._state_key, self.cooldown_sec, "CLOSED")
        self._setex(self._fail_key, self.cooldown_sec, "0")

    def record_failure(self) -> None:
        try:
            fails = int(self._get(self._fail_key) or "0") + 1
        except Exception:
            fails = 1
        self._setex(self._fail_key, self.cooldown_sec, str(fails))
        if fails >= self.failure_threshold:
            self._setex(self._state_key, self.cooldown_sec, "OPEN")
            self._setex(self._until_key, self.cooldown_sec, str(_now() + self.cooldown_sec))


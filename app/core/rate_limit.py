import time


class InMemoryThrottle:
    """Simple per-key cooldown throttle. Not distributed, resets on process restart."""

    def __init__(self, min_interval_seconds: float) -> None:
        self._min_interval = min_interval_seconds
        self._last_seen: dict[str, float] = {}

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        last = self._last_seen.get(key)
        if last is not None and (now - last) < self._min_interval:
            return False
        self._last_seen[key] = now
        return True

    def reset(self) -> None:
        self._last_seen.clear()

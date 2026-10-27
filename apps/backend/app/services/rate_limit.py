"""Oddiy xotiradagi urinishlar cheklovi (bitta jarayon uchun MVP)."""
import time
from collections import defaultdict, deque


class AttemptLimiter:
    def __init__(self) -> None:
        self._failures: dict[str, deque[float]] = defaultdict(deque)

    def _prune(self, key: str, window: int) -> deque[float]:
        q = self._failures[key]
        cutoff = time.monotonic() - window
        while q and q[0] < cutoff:
            q.popleft()
        return q

    def retry_after(self, key: str, max_attempts: int, window: int) -> int:
        """Bloklangan bo'lsa — necha soniyadan keyin qayta urinish mumkin, aks holda 0."""
        q = self._prune(key, window)
        if len(q) < max_attempts:
            return 0
        return max(1, int(q[0] + window - time.monotonic()))

    def record_failure(self, key: str) -> None:
        self._failures[key].append(time.monotonic())

    def reset(self, key: str | None = None) -> None:
        if key is None:
            self._failures.clear()
        else:
            self._failures.pop(key, None)


login_limiter = AttemptLimiter()

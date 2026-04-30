from dataclasses import dataclass
from time import monotonic
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    expires_at: float
    value: T


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: int, max_items: int = 512) -> None:
        self.ttl_seconds = ttl_seconds
        self.max_items = max_items
        self._items: dict[str, CacheEntry[T]] = {}

    def get(self, key: str) -> T | None:
        entry = self._items.get(key)
        if entry is None:
            return None

        if entry.expires_at <= monotonic():
            self._items.pop(key, None)
            return None

        return entry.value

    def set(self, key: str, value: T) -> None:
        if len(self._items) >= self.max_items:
            self._prune()

        self._items[key] = CacheEntry(
            expires_at=monotonic() + self.ttl_seconds,
            value=value,
        )

    def _prune(self) -> None:
        now = monotonic()
        expired_keys = [key for key, entry in self._items.items() if entry.expires_at <= now]
        for key in expired_keys:
            self._items.pop(key, None)

        while len(self._items) >= self.max_items:
            oldest_key = min(self._items, key=lambda key: self._items[key].expires_at)
            self._items.pop(oldest_key, None)

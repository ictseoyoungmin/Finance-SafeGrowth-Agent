"""Simple in-memory TTL + LRU cache shared by analyze / rewrite services.

Replace with Redis later; the interface stays the same.
"""

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Generic, TypeVar


DEFAULT_TTL_SECONDS = 15 * 60
DEFAULT_MAX_ENTRIES = 256


T = TypeVar("T")


@dataclass
class _Entry(Generic[T]):
    value: T
    expires_at: float


class ResponseCache(Generic[T]):
    def __init__(
        self,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ) -> None:
        self._ttl = ttl_seconds
        self._max = max(1, max_entries)
        self._store: "OrderedDict[str, _Entry[T]]" = OrderedDict()
        self.hits = 0
        self.misses = 0

    @property
    def ttl_seconds(self) -> int:
        return self._ttl

    @property
    def max_entries(self) -> int:
        return self._max

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            self.misses += 1
            return None
        if time.monotonic() >= entry.expires_at:
            self._store.pop(key, None)
            self.misses += 1
            return None
        # LRU: mark as most-recently-used
        self._store.move_to_end(key)
        self.hits += 1
        return entry.value

    def set(self, key: str, value: T) -> None:
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = _Entry(value=value, expires_at=time.monotonic() + self._ttl)
        # Evict oldest until within cap.
        while len(self._store) > self._max:
            self._store.popitem(last=False)

    def clear(self) -> None:
        self._store.clear()
        self.hits = 0
        self.misses = 0

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        hit_rate = round(self.hits / total, 4) if total else 0.0
        return {
            "entries": len(self._store),
            "max_entries": self._max,
            "ttl_seconds": self._ttl,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
        }

    def __len__(self) -> int:
        return len(self._store)

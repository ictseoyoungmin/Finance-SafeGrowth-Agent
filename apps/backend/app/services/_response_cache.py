"""Simple in-memory TTL cache shared by analyze / rewrite services.

Replace with Redis later; the interface stays the same.
"""

import time
from dataclasses import dataclass
from typing import Generic, TypeVar


DEFAULT_TTL_SECONDS = 15 * 60


T = TypeVar("T")


@dataclass
class _Entry(Generic[T]):
    value: T
    expires_at: float


class ResponseCache(Generic[T]):
    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._ttl = ttl_seconds
        self._store: dict[str, _Entry[T]] = {}

    @property
    def ttl_seconds(self) -> int:
        return self._ttl

    def get(self, key: str) -> T | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: T) -> None:
        self._store[key] = _Entry(value=value, expires_at=time.monotonic() + self._ttl)

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

import asyncio
import time
from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    value: T
    fetched_at: float


class MemoryCache(Generic[T]):
    def __init__(self, ttl_seconds: int):
        self.ttl_seconds = ttl_seconds
        self._entries: dict[str, CacheEntry[T]] = {}

    def get(self, key: str) -> CacheEntry[T] | None:
        return self._entries.get(key)

    def is_fresh(self, entry: CacheEntry[T]) -> bool:
        return time.monotonic() - entry.fetched_at < self.ttl_seconds

    def set(self, key: str, value: T) -> CacheEntry[T]:
        entry = CacheEntry(value=value, fetched_at=time.monotonic())
        self._entries[key] = entry
        return entry


class LockedMemoryCache(MemoryCache[T]):
    def __init__(self, ttl_seconds: int):
        super().__init__(ttl_seconds)
        self.lock = asyncio.Lock()

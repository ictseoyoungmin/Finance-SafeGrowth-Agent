import time

from app.services._response_cache import ResponseCache


def test_cache_set_get_hit() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_seconds=60)
    cache.set("k", "v")
    assert cache.get("k") == "v"


def test_cache_miss_on_unknown_key() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_seconds=60)
    assert cache.get("missing") is None


def test_cache_expires_after_ttl() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_seconds=0)
    cache.set("k", "v")
    # ttl 0 means it expires by the time we read it (monotonic >= expires_at).
    # Sleep a tick to guarantee the comparison.
    time.sleep(0.01)
    assert cache.get("k") is None


def test_cache_clear() -> None:
    cache: ResponseCache[str] = ResponseCache()
    cache.set("k", "v")
    cache.clear()
    assert cache.get("k") is None
    assert len(cache) == 0


def test_cache_evicts_oldest_over_max_entries() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_seconds=60, max_entries=2)
    cache.set("a", "1")
    cache.set("b", "2")
    cache.set("c", "3")  # exceeds cap → oldest "a" evicted
    assert cache.get("a") is None
    assert cache.get("b") == "2"
    assert cache.get("c") == "3"
    assert len(cache) == 2


def test_cache_lru_keeps_recently_used() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_seconds=60, max_entries=2)
    cache.set("a", "1")
    cache.set("b", "2")
    # touch "a" → now "b" is the oldest
    assert cache.get("a") == "1"
    cache.set("c", "3")  # evicts "b" (least recently used)
    assert cache.get("b") is None
    assert cache.get("a") == "1"
    assert cache.get("c") == "3"


def test_cache_stats_counts_hits_and_misses() -> None:
    cache: ResponseCache[str] = ResponseCache(ttl_seconds=60, max_entries=8)
    cache.set("k", "v")
    cache.get("k")        # hit
    cache.get("missing")  # miss
    stats = cache.stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.5
    assert stats["entries"] == 1
    assert stats["max_entries"] == 8

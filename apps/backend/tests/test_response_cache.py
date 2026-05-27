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

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "env": "development"}


def test_cache_stats_endpoint_shape() -> None:
    client = TestClient(app)

    response = client.get("/v1/health/cache-stats")

    assert response.status_code == 200
    body = response.json()
    for bucket in ("analyze", "rewrite"):
        assert bucket in body
        assert {"entries", "max_entries", "ttl_seconds", "hits", "misses", "hit_rate"} <= set(
            body[bucket]
        )

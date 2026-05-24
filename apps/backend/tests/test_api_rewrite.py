from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.repositories.contents_repo import get_content_repository
from app.repositories.regulation_docs_repo import get_regulation_docs_repository
from app.repositories.risk_results_repo import get_risk_results_repository
from app.services.rewrite_service import RewriteService, get_rewrite_service
from tests._agent_fakes import ScriptedLlmProvider


@pytest.fixture(autouse=True)
def fallback_rewrite_service_override():
    app.dependency_overrides[get_rewrite_service] = lambda: RewriteService(
        llm_provider=ScriptedLlmProvider(configured=False),
        content_repository=get_content_repository(),
        risk_results_repository=get_risk_results_repository(),
        regulation_docs_repository=get_regulation_docs_repository(),
    )
    yield
    app.dependency_overrides.pop(get_rewrite_service, None)


def test_rewrite_returns_fallback_without_llm() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/compliance/rewrite",
        json={"content_id": "demo-content", "mode": "marketing_balanced"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["content_id"] == "demo-content"
    assert body["revised_text_conservative"]
    assert body["revised_text_marketing"]
    assert len(body["changes"]) >= 1
    assert body["source"] == "fallback"

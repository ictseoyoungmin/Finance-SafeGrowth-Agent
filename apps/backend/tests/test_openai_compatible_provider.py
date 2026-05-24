import json
from typing import Any

from app.integrations.llm.openai_compatible import OpenAICompatibleLlmProvider


class FakeResponse:
    def __init__(self, payload: dict[str, Any], status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise AssertionError(f"unexpected status: {self.status_code}")

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeHttpxClient:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.posts: list[dict[str, Any]] = []
        self.gets: list[str] = []

    def post(self, url: str, **kwargs: Any) -> FakeResponse:
        self.posts.append({"url": url, **kwargs})
        return FakeResponse(self.payload)

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        self.gets.append(url)
        return FakeResponse({"status": "ok"})


def test_generate_json_posts_openai_chat_request_and_parses_json() -> None:
    client = FakeHttpxClient(
        {
            "model": "gemma-4-local",
            "choices": [{"message": {"content": '```json\n{"ok": true}\n```'}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2},
        }
    )
    provider = OpenAICompatibleLlmProvider(
        base_url="http://local.test/v1",
        api_key="local-not-required",
        model="gemma-4-local",
        client=client,  # type: ignore[arg-type]
    )

    result = provider.generate_json('{"task":"ping"}')

    assert result is not None
    assert result.payload == {"ok": True}
    assert client.posts[0]["url"] == "http://local.test/v1/chat/completions"
    body = client.posts[0]["json"]
    assert body["model"] == "gemma-4-local"
    assert body["thinking"] is False
    assert body["chat_template_kwargs"] == {"enable_thinking": False}


def test_generate_with_tools_converts_transcript_and_reads_tool_call() -> None:
    client = FakeHttpxClient(
        {
            "model": "gemma-4-local",
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "scan_rules",
                                    "arguments": json.dumps({"text": "demo"}),
                                },
                            }
                        ]
                    }
                }
            ],
            "usage": {"prompt_tokens": 11, "completion_tokens": 7},
        }
    )
    provider = OpenAICompatibleLlmProvider(
        base_url="http://local.test/v1",
        api_key="local-not-required",
        model="gemma-4-local",
        client=client,  # type: ignore[arg-type]
    )

    response = provider.generate_with_tools(
        messages=[
            {"role": "user", "parts": [{"text": "검토해줘"}]},
            {
                "role": "model",
                "parts": [{"functionCall": {"name": "scan_rules", "args": {"text": "검토해줘"}}}],
            },
            {
                "role": "user",
                "parts": [{"functionResponse": {"name": "scan_rules", "response": {"risk_level": "LOW"}}}],
            },
        ],
        function_declarations=[
            {
                "name": "scan_rules",
                "description": "Scan text.",
                "parameters": {
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            }
        ],
        system_instruction="system",
    )

    assert response is not None
    assert response.function_call is not None
    assert response.function_call.name == "scan_rules"
    assert response.function_call.args == {"text": "demo"}
    assert response.input_tokens == 11
    assert response.output_tokens == 7

    body = client.posts[0]["json"]
    assert body["messages"][0] == {"role": "system", "content": "system"}
    assert body["messages"][2]["tool_calls"][0]["function"]["name"] == "scan_rules"
    assert body["messages"][3]["role"] == "tool"
    assert body["tools"][0]["type"] == "function"


def test_openai_compatible_healthcheck_uses_configured_base_url() -> None:
    client = FakeHttpxClient({"choices": []})
    provider = OpenAICompatibleLlmProvider(
        base_url="http://local.test/v1",
        api_key="local-not-required",
        model="gemma-4-local",
        client=client,  # type: ignore[arg-type]
    )

    assert provider.healthcheck() is True
    assert client.gets == ["http://local.test/v1/health"]

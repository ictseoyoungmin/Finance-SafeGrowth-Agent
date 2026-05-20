from app.integrations.gemini_client import GeminiClient, parse_json_payload


def test_parse_json_payload_accepts_raw_json() -> None:
    assert parse_json_payload('{"key":"value"}') == {"key": "value"}


def test_parse_json_payload_accepts_fenced_json() -> None:
    assert parse_json_payload('```json\n{"key":"value"}\n```') == {"key": "value"}


def test_parse_json_payload_accepts_explained_json_substring() -> None:
    assert parse_json_payload('Here is the JSON:\n{"key":"value"}\nThanks') == {"key": "value"}


def test_parse_json_payload_rejects_non_object_json() -> None:
    assert parse_json_payload('["value"]') is None


def test_gemini_placeholder_key_is_not_configured() -> None:
    client = GeminiClient(api_key="replace-me", model="gemini-test")

    assert client.is_configured is False
    assert client.generate_json('{"task":"test"}') is None

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from app.core.config import settings


@dataclass(frozen=True)
class GeminiResult:
    payload: dict[str, Any]
    model_version: str


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or settings.gemini_api_key
        self._model = model or settings.gemini_model

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def generate_json(self, prompt: str) -> GeminiResult | None:
        if not self._api_key:
            return None

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={self._api_key}"
        )
        body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            return None

        text = self._extract_text(raw)
        if not text:
            return None

        payload = parse_json_payload(text)
        if payload is None:
            return None

        return GeminiResult(payload=payload, model_version=self._model)

    def _extract_text(self, raw: dict[str, Any]) -> str | None:
        candidates = raw.get("candidates") or []
        if not candidates:
            return None

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return None

        text = parts[0].get("text")
        return text if isinstance(text, str) else None


def parse_json_payload(text: str) -> dict[str, Any] | None:
    direct = _loads_object(text.strip())
    if direct is not None:
        return direct

    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        fenced = _loads_object("\n".join(lines).strip())
        if fenced is not None:
            return fenced

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return _loads_object(text[start : end + 1])

    return None


def _loads_object(text: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def get_gemini_client() -> GeminiClient:
    return GeminiClient()

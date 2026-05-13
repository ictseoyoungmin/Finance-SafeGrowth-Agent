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

        try:
            return GeminiResult(payload=json.loads(text), model_version=self._model)
        except json.JSONDecodeError:
            return None

    def _extract_text(self, raw: dict[str, Any]) -> str | None:
        candidates = raw.get("candidates") or []
        if not candidates:
            return None

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            return None

        text = parts[0].get("text")
        return text if isinstance(text, str) else None


def get_gemini_client() -> GeminiClient:
    return GeminiClient()

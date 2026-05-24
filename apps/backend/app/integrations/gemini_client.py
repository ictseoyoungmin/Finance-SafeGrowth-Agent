import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.supabase_client import is_real_value


logger = get_logger(__name__)


@dataclass(frozen=True)
class GeminiResult:
    payload: dict[str, Any]
    model_version: str


@dataclass(frozen=True)
class GeminiFunctionCall:
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class GeminiToolResponse:
    function_call: GeminiFunctionCall | None
    text: str | None
    input_tokens: int
    output_tokens: int
    model_version: str
    raw: dict[str, Any] = field(default_factory=dict)


class GeminiClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or settings.gemini_api_key
        self._model = model or settings.gemini_model

    @property
    def model(self) -> str:
        return self._model

    @property
    def is_configured(self) -> bool:
        return is_real_value(self._api_key)

    def generate_json(self, prompt: str) -> GeminiResult | None:
        if not self.is_configured:
            return None

        body = {"contents": [{"parts": [{"text": prompt}]}]}
        raw = self._post(body)
        if raw is None:
            return None

        text = self._extract_text(raw)
        if not text:
            logger.warning("Gemini response did not contain text output.")
            return None

        payload = parse_json_payload(text)
        if payload is None:
            logger.warning("Gemini returned non-parseable JSON.")
            return None

        return GeminiResult(payload=payload, model_version=self._model)

    def generate_with_tools(
        self,
        contents: list[dict[str, Any]],
        function_declarations: list[dict[str, Any]],
        *,
        system_instruction: str | None = None,
        tool_config: dict[str, Any] | None = None,
        temperature: float = 0.2,
    ) -> GeminiToolResponse | None:
        if not self.is_configured:
            return None

        body: dict[str, Any] = {
            "contents": contents,
            "tools": [{"functionDeclarations": function_declarations}],
            "generationConfig": {"temperature": temperature},
        }
        if system_instruction:
            body["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        if tool_config:
            body["toolConfig"] = tool_config

        raw = self._post(body)
        if raw is None:
            return None

        function_call = _extract_function_call(raw)
        text = self._extract_text(raw) if function_call is None else None
        usage = raw.get("usageMetadata") or {}

        return GeminiToolResponse(
            function_call=function_call,
            text=text,
            input_tokens=int(usage.get("promptTokenCount") or 0),
            output_tokens=int(usage.get("candidatesTokenCount") or 0),
            model_version=self._model,
            raw=raw,
        )

    def _post(self, body: dict[str, Any]) -> dict[str, Any] | None:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={self._api_key}"
        )
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            logger.exception("Gemini call failed.")
            return None

    def _extract_text(self, raw: dict[str, Any]) -> str | None:
        candidates = raw.get("candidates") or []
        if not candidates:
            return None

        parts = candidates[0].get("content", {}).get("parts", [])
        for part in parts:
            text = part.get("text") if isinstance(part, dict) else None
            if isinstance(text, str) and text:
                return text
        return None


def _extract_function_call(raw: dict[str, Any]) -> GeminiFunctionCall | None:
    candidates = raw.get("candidates") or []
    if not candidates:
        return None

    parts = candidates[0].get("content", {}).get("parts", [])
    for part in parts:
        if not isinstance(part, dict):
            continue
        call = part.get("functionCall")
        if not isinstance(call, dict):
            continue
        name = call.get("name")
        args = call.get("args")
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}
        if not isinstance(args, dict):
            args = {}
        if isinstance(name, str) and name:
            return GeminiFunctionCall(name=name, args=args)
    return None


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

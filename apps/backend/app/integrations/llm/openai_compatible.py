import json
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.gemini_client import parse_json_payload
from app.integrations.llm.base import (
    LlmFunctionCall,
    LlmJsonResult,
    LlmMessage,
    LlmToolResponse,
)
from app.integrations.supabase_client import is_real_value


logger = get_logger(__name__)


class OpenAICompatibleLlmProvider:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float | None = None,
        thinking_enabled: bool | None = None,
        max_tokens: int | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = (base_url or settings.openai_base_url).rstrip("/")
        self._api_key = api_key if api_key is not None else settings.openai_api_key
        self._model = model or settings.openai_model
        self._timeout_seconds = timeout_seconds or settings.llm_timeout_seconds
        self._thinking_enabled = (
            settings.llm_thinking_enabled if thinking_enabled is None else thinking_enabled
        )
        self._max_tokens = max_tokens or settings.llm_max_tokens
        self._client = client

    @property
    def model(self) -> str:
        return self._model

    @property
    def is_configured(self) -> bool:
        return bool(self._base_url and self._model and is_real_value(self._api_key))

    def generate_json(self, prompt: str) -> LlmJsonResult | None:
        if not self.is_configured:
            return None

        raw = self._post_chat(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": "Return only raw JSON. Do not use markdown.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": settings.llm_temperature,
            }
        )
        if raw is None:
            return None

        text = _extract_message_content(raw)
        if not text:
            logger.warning("OpenAI-compatible response did not contain text output.")
            return None

        payload = parse_json_payload(text)
        if payload is None:
            logger.warning("OpenAI-compatible provider returned non-parseable JSON.")
            return None
        return LlmJsonResult(payload=payload, model_version=self._model)

    def generate_with_tools(
        self,
        messages: list[LlmMessage],
        function_declarations: list[dict[str, Any]],
        *,
        system_instruction: str | None = None,
        tool_config: dict[str, Any] | None = None,
        temperature: float = 0.2,
    ) -> LlmToolResponse | None:
        if not self.is_configured:
            return None

        raw = self._post_chat(
            {
                "messages": _to_openai_messages(messages, system_instruction),
                "tools": [_to_openai_tool(declaration) for declaration in function_declarations],
                "tool_choice": _tool_choice(tool_config),
                "temperature": temperature,
            }
        )
        if raw is None:
            return None

        message = _first_choice_message(raw)
        function_call = _extract_tool_call(message)
        usage = raw.get("usage") or {}
        return LlmToolResponse(
            function_call=function_call,
            text=message.get("content") if isinstance(message.get("content"), str) else None,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            model_version=str(raw.get("model") or self._model),
            raw=raw,
        )

    def healthcheck(self) -> bool:
        if not self.is_configured:
            return False
        try:
            response = self._request_client().get(
                f"{self._base_url}/health",
                headers=self._headers(),
                timeout=self._timeout_seconds,
            )
            return response.status_code < 500
        except httpx.HTTPError:
            return False

    def _post_chat(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        body = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            **payload,
            **self._thinking_body(),
        }
        try:
            response = self._request_client().post(
                f"{self._base_url}/chat/completions",
                json=body,
                headers=self._headers(),
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, json.JSONDecodeError):
            logger.exception("OpenAI-compatible LLM call failed.")
            return None

    def _request_client(self) -> httpx.Client:
        return self._client or httpx.Client()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    def _thinking_body(self) -> dict[str, Any]:
        return {
            "thinking": self._thinking_enabled,
            "chat_template_kwargs": {"enable_thinking": self._thinking_enabled},
        }


def _to_openai_messages(
    messages: list[LlmMessage],
    system_instruction: str | None,
) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    if system_instruction:
        converted.append({"role": "system", "content": system_instruction})

    pending_tool_calls: list[tuple[str, str]] = []
    for index, message in enumerate(messages):
        role = message.get("role")
        parts = message.get("parts") or []
        text = _parts_text(parts)

        function_call = _part_value(parts, "functionCall")
        function_response = _part_value(parts, "functionResponse")
        if isinstance(function_call, dict):
            name = str(function_call.get("name") or "")
            call_id = f"call_{index}_{name or 'tool'}"
            converted.append(
                {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": json.dumps(function_call.get("args") or {}, ensure_ascii=False),
                            },
                        }
                    ],
                }
            )
            pending_tool_calls.append((name, call_id))
        elif isinstance(function_response, dict):
            name = str(function_response.get("name") or "")
            _, call_id = pending_tool_calls.pop(0) if pending_tool_calls else (name, f"call_{index}_{name}")
            converted.append(
                {
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": json.dumps(function_response.get("response") or {}, ensure_ascii=False),
                }
            )
        elif text:
            converted.append({"role": "assistant" if role == "model" else "user", "content": text})

    return converted or [{"role": "user", "content": "Please review the supplied content."}]


def _parts_text(parts: list[Any]) -> str:
    texts: list[str] = []
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            texts.append(part["text"])
    return "\n".join(texts)


def _part_value(parts: list[Any], key: str) -> Any:
    for part in parts:
        if isinstance(part, dict) and key in part:
            return part[key]
    return None


def _to_openai_tool(declaration: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": declaration.get("name"),
            "description": declaration.get("description") or "",
            "parameters": declaration.get("parameters") or {"type": "object", "properties": {}},
        },
    }


def _tool_choice(tool_config: dict[str, Any] | None) -> str | dict[str, Any]:
    if not tool_config:
        return "auto"
    allowed = (
        tool_config.get("functionCallingConfig", {}).get("allowedFunctionNames")
        if isinstance(tool_config.get("functionCallingConfig"), dict)
        else None
    )
    if isinstance(allowed, list) and len(allowed) == 1:
        return {"type": "function", "function": {"name": allowed[0]}}
    return "auto"


def _first_choice_message(raw: dict[str, Any]) -> dict[str, Any]:
    choices = raw.get("choices") or []
    if not choices:
        return {}
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    return message if isinstance(message, dict) else {}


def _extract_tool_call(message: dict[str, Any]) -> LlmFunctionCall | None:
    tool_calls = message.get("tool_calls") or []
    if not tool_calls:
        return None

    call = tool_calls[0]
    function = call.get("function") if isinstance(call, dict) else None
    if not isinstance(function, dict):
        return None

    name = function.get("name")
    args = function.get("arguments") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            args = {}
    if not isinstance(args, dict):
        args = {}
    return LlmFunctionCall(name=name, args=args) if isinstance(name, str) and name else None


def _extract_message_content(raw: dict[str, Any]) -> str | None:
    message = _first_choice_message(raw)
    content = message.get("content")
    return content if isinstance(content, str) and content else None

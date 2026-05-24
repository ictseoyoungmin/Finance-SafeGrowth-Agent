from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel

from app.agent.state import AgentState


class ToolError(Exception):
    def __init__(
        self,
        code: str,
        message: str = "",
        *,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message or code)
        self.code = code
        self.message = message or code
        self.retryable = retryable
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        return {
            "error": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "details": self.details,
        }


@runtime_checkable
class Tool(Protocol):
    name: str
    description: str
    args_model: type[BaseModel]
    result_model: type[BaseModel] | None

    def run(self, args: BaseModel, state: AgentState) -> BaseModel: ...


def to_gemini_schema(model_cls: type[BaseModel]) -> dict[str, Any]:
    """Convert a Pydantic model into a Gemini-compatible JSON schema dict.

    Gemini function declarations accept a subset of OpenAPI 3.0 schema. This
    helper inlines `$defs`, strips unsupported fields, and returns a plain dict
    that the Day 17 agent runner can hand to `Tool(function_declarations=[...])`.
    """

    schema = model_cls.model_json_schema()
    defs = schema.pop("$defs", {})
    inlined = _inline_refs(schema, defs)
    return _sanitize(inlined)


def gemini_declaration(tool: Tool) -> dict[str, Any]:
    return {
        "name": tool.name,
        "description": tool.description.strip(),
        "parameters": to_gemini_schema(tool.args_model),
    }


def _inline_refs(node: Any, defs: dict[str, Any]) -> Any:
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            target_name = ref.rsplit("/", 1)[-1]
            target = defs.get(target_name, {})
            resolved = _inline_refs(target, defs)
            extra = {key: _inline_refs(value, defs) for key, value in node.items() if key != "$ref"}
            if isinstance(resolved, dict):
                merged = dict(resolved)
                merged.update(extra)
                return merged
            return resolved
        return {key: _inline_refs(value, defs) for key, value in node.items()}
    if isinstance(node, list):
        return [_inline_refs(item, defs) for item in node]
    return node


_DROP_KEYS = {"title", "$defs", "definitions"}


def _sanitize(node: Any) -> Any:
    if isinstance(node, dict):
        if "anyOf" in node:
            return _collapse_any_of(node)
        cleaned: dict[str, Any] = {}
        for key, value in node.items():
            if key in _DROP_KEYS:
                continue
            cleaned[key] = _sanitize(value)
        return cleaned
    if isinstance(node, list):
        return [_sanitize(item) for item in node]
    return node


def _collapse_any_of(node: dict[str, Any]) -> dict[str, Any]:
    options = node.get("anyOf", [])
    nullable = any(isinstance(option, dict) and option.get("type") == "null" for option in options)
    non_null = [option for option in options if not (isinstance(option, dict) and option.get("type") == "null")]
    base = _sanitize(non_null[0]) if non_null else {}
    if not isinstance(base, dict):
        base = {}
    extras = {key: _sanitize(value) for key, value in node.items() if key not in {"anyOf"}}
    base.update(extras)
    base.pop("title", None)
    if nullable:
        base["nullable"] = True
    return base

from pydantic import BaseModel

from app.agent.state import init_state
from app.agent.tools.base import ToolError, gemini_declaration, to_gemini_schema
from app.agent.tools.registry import ToolRegistry
from app.schemas.agent import AgentRunRequest
from app.schemas.tools import (
    DraftRewriteArgs,
    FinalizeReportArgs,
    RequestHumanReviewArgs,
    ScanRulesArgs,
    SearchRegulationArgs,
)


class _EchoArgs(BaseModel):
    value: str


class _EchoResult(BaseModel):
    echoed: str


class EchoTool:
    name = "echo"
    description = "Return the value passed in."
    args_model = _EchoArgs
    result_model = _EchoResult

    def __init__(self, *, fail: bool = False, raise_tool_error: bool = False) -> None:
        self._fail = fail
        self._raise_tool_error = raise_tool_error

    def run(self, args: _EchoArgs, state) -> _EchoResult:
        if self._raise_tool_error:
            raise ToolError("custom_error", "boom", details={"k": "v"})
        if self._fail:
            raise RuntimeError("upstream boom")
        return _EchoResult(echoed=args.value)


def _state() -> object:
    return init_state(AgentRunRequest(text="demo"))


def test_registry_invoke_returns_serialized_result() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    payload = registry.invoke("echo", {"value": "hello"}, _state())

    assert payload == {"echoed": "hello"}


def test_registry_invoke_unknown_tool() -> None:
    registry = ToolRegistry()

    payload = registry.invoke("missing", {}, _state())

    assert payload["error"] == "unknown_tool"


def test_registry_invoke_invalid_args() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    payload = registry.invoke("echo", {}, _state())

    assert payload["error"] == "invalid_args"
    assert "errors" in payload["details"]


def test_registry_invoke_upstream_failure_maps_to_retryable_error() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool(fail=True))

    payload = registry.invoke("echo", {"value": "x"}, _state())

    assert payload["error"] == "upstream_failed"
    assert payload["retryable"] is True
    assert payload["details"]["type"] == "RuntimeError"


def test_registry_invoke_propagates_tool_error_payload() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool(raise_tool_error=True))

    payload = registry.invoke("echo", {"value": "x"}, _state())

    assert payload["error"] == "custom_error"
    assert payload["message"] == "boom"
    assert payload["details"] == {"k": "v"}


def test_registry_rejects_duplicate_registration() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    try:
        registry.register(EchoTool())
    except ValueError as exc:
        assert "already registered" in str(exc)
    else:  # pragma: no cover - safety net
        raise AssertionError("Expected ValueError on duplicate tool registration.")


def test_default_registry_lists_all_six_tools() -> None:
    from app.agent.tools import get_default_registry

    registry = get_default_registry()

    assert set(registry.names()) == {
        "fetch_content",
        "scan_rules",
        "search_regulation",
        "draft_rewrite",
        "request_human_review",
        "finalize_report",
    }


def test_gemini_declaration_shape_for_each_tool() -> None:
    from app.agent.tools import get_default_registry

    declarations = get_default_registry().declarations()
    by_name = {decl["name"]: decl for decl in declarations}

    for name in (
        "fetch_content",
        "scan_rules",
        "search_regulation",
        "draft_rewrite",
        "request_human_review",
        "finalize_report",
    ):
        decl = by_name[name]
        assert decl["description"].strip()
        params = decl["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "$defs" not in params
        assert "$ref" not in _flatten_keys(params)


def test_to_gemini_schema_handles_nested_models() -> None:
    schema = to_gemini_schema(SearchRegulationArgs)

    assert schema["type"] == "object"
    assert "risk_categories" in schema["properties"]
    assert schema["properties"]["risk_categories"]["type"] == "array"
    assert schema["properties"]["risk_categories"]["items"]["type"] == "string"


def test_to_gemini_schema_collapses_optional_into_nullable() -> None:
    schema = to_gemini_schema(RequestHumanReviewArgs)

    options_prop = schema["properties"]["options"]
    assert options_prop["type"] == "array"
    assert options_prop.get("nullable") is True

    proposed = schema["properties"]["proposed_action"]
    assert proposed["type"] == "object"
    assert proposed.get("nullable") is True


def test_gemini_declaration_required_fields() -> None:
    declarations = {
        tool.__name__: gemini_declaration(_DummyTool(args_model))
        for tool, args_model in [
            (ScanRulesArgs, ScanRulesArgs),
            (DraftRewriteArgs, DraftRewriteArgs),
            (FinalizeReportArgs, FinalizeReportArgs),
        ]
    }
    assert "text" in declarations["ScanRulesArgs"]["parameters"]["required"]
    assert "content_id" in declarations["DraftRewriteArgs"]["parameters"]["required"]
    assert "content_id" in declarations["FinalizeReportArgs"]["parameters"]["required"]


class _DummyTool:
    description = "dummy"

    def __init__(self, args_model) -> None:
        self.args_model = args_model
        self.result_model = None
        self.name = args_model.__name__


def _flatten_keys(node) -> list[str]:
    keys: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            keys.append(key)
            keys.extend(_flatten_keys(value))
    elif isinstance(node, list):
        for item in node:
            keys.extend(_flatten_keys(item))
    return keys

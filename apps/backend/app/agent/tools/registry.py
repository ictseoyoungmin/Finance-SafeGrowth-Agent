from typing import Any

from pydantic import BaseModel, ValidationError

from app.agent.state import AgentState
from app.agent.tools.base import Tool, ToolError, gemini_declaration


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def declarations(self) -> list[dict[str, Any]]:
        return [gemini_declaration(tool) for tool in self._tools.values()]

    def invoke(
        self,
        name: str,
        raw_args: dict[str, Any],
        state: AgentState,
    ) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            return ToolError("unknown_tool", f"Tool '{name}' is not registered.").to_payload()

        try:
            args = tool.args_model.model_validate(raw_args or {})
        except ValidationError as exc:
            return ToolError(
                "invalid_args",
                f"Invalid arguments for tool '{name}'.",
                details={"errors": exc.errors()},
            ).to_payload()

        try:
            result = tool.run(args, state)
        except ToolError as exc:
            return exc.to_payload()
        except Exception as exc:  # noqa: BLE001
            return ToolError(
                "upstream_failed",
                str(exc) or "Tool execution failed.",
                retryable=True,
                details={"type": exc.__class__.__name__},
            ).to_payload()

        if tool.result_model is not None and not isinstance(result, tool.result_model):
            return ToolError(
                "invalid_result",
                f"Tool '{name}' returned an unexpected result type.",
            ).to_payload()

        if isinstance(result, BaseModel):
            return result.model_dump(mode="json")
        return dict(result) if isinstance(result, dict) else {"value": result}

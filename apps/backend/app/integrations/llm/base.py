from dataclasses import dataclass, field
from typing import Any, Protocol


LlmMessage = dict[str, Any]


@dataclass(frozen=True)
class LlmJsonResult:
    payload: dict[str, Any]
    model_version: str


@dataclass(frozen=True)
class LlmFunctionCall:
    name: str
    args: dict[str, Any]


@dataclass(frozen=True)
class LlmToolResponse:
    function_call: LlmFunctionCall | None
    text: str | None
    input_tokens: int
    output_tokens: int
    model_version: str
    raw: dict[str, Any] = field(default_factory=dict)


class LlmProvider(Protocol):
    @property
    def model(self) -> str: ...

    @property
    def is_configured(self) -> bool: ...

    def generate_json(self, prompt: str) -> LlmJsonResult | None: ...

    def generate_with_tools(
        self,
        messages: list[LlmMessage],
        function_declarations: list[dict[str, Any]],
        *,
        system_instruction: str | None = None,
        tool_config: dict[str, Any] | None = None,
        temperature: float = 0.2,
    ) -> LlmToolResponse | None: ...

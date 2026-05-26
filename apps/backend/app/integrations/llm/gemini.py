from typing import Any

from app.integrations.gemini_client import GeminiAttempt, GeminiClient
from app.integrations.llm.base import (
    LlmAttempt,
    LlmFunctionCall,
    LlmJsonResult,
    LlmMessage,
    LlmToolResponse,
)


def _to_llm_attempts(attempts: list[GeminiAttempt]) -> list[LlmAttempt]:
    return [
        LlmAttempt(
            model=item.model,
            status=item.status,
            error_code=item.error_code,
            detail=item.detail,
        )
        for item in attempts
    ]


class GeminiLlmProvider:
    def __init__(self, client: GeminiClient | None = None) -> None:
        self._client = client or GeminiClient()

    @property
    def model(self) -> str:
        return self._client.model

    @property
    def is_configured(self) -> bool:
        return self._client.is_configured

    def generate_json(self, prompt: str) -> LlmJsonResult | None:
        result = self._client.generate_json(prompt)
        if result is None:
            return None
        return LlmJsonResult(
            payload=result.payload,
            model_version=result.model_version,
            attempts=_to_llm_attempts(result.attempts),
        )

    def generate_with_tools(
        self,
        messages: list[LlmMessage],
        function_declarations: list[dict[str, Any]],
        *,
        system_instruction: str | None = None,
        tool_config: dict[str, Any] | None = None,
        temperature: float = 0.2,
    ) -> LlmToolResponse | None:
        response = self._client.generate_with_tools(
            contents=messages,
            function_declarations=function_declarations,
            system_instruction=system_instruction,
            tool_config=tool_config,
            temperature=temperature,
        )
        if response is None:
            return None

        function_call = (
            LlmFunctionCall(
                name=response.function_call.name,
                args=response.function_call.args,
            )
            if response.function_call
            else None
        )
        return LlmToolResponse(
            function_call=function_call,
            text=response.text,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            model_version=response.model_version,
            raw=response.raw,
            attempts=_to_llm_attempts(response.attempts),
        )

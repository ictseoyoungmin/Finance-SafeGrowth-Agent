from typing import Any, Protocol
from uuid import UUID

from app.repositories.agent_steps_repo import (
    AgentStepsRepository,
    get_agent_steps_repository,
)
from app.schemas.agent import AgentStep, AgentStepType


class TraceRecorder(Protocol):
    def record_thought(self, run_id: UUID, step_index: int, text: str) -> AgentStep: ...

    def record_tool_call(
        self,
        run_id: UUID,
        step_index: int,
        tool_name: str,
        args: dict[str, Any],
    ) -> AgentStep: ...

    def record_tool_result(
        self,
        run_id: UUID,
        step_index: int,
        tool_name: str,
        result: dict[str, Any],
    ) -> AgentStep: ...

    def record_human_prompt(
        self,
        run_id: UUID,
        step_index: int,
        prompt: dict[str, Any],
    ) -> AgentStep: ...

    def record_human_response(
        self,
        run_id: UUID,
        step_index: int,
        response: dict[str, Any],
    ) -> AgentStep: ...

    def record_final(
        self,
        run_id: UUID,
        step_index: int,
        final: dict[str, Any],
    ) -> AgentStep: ...

    def list_steps(self, run_id: UUID) -> list[AgentStep]: ...


class InMemoryTraceRecorder:
    def __init__(self) -> None:
        self._steps: dict[str, list[AgentStep]] = {}

    def _append(
        self,
        run_id: UUID,
        step_index: int,
        step_type: AgentStepType,
        payload: dict[str, Any],
        tool_name: str | None = None,
    ) -> AgentStep:
        step = AgentStep(
            run_id=run_id,
            step_index=step_index,
            step_type=step_type,
            tool_name=tool_name,
            payload=payload,
        )
        bucket = self._steps.setdefault(str(run_id), [])
        if bucket and step_index <= bucket[-1].step_index:
            raise ValueError(
                f"step_index must be strictly increasing; got {step_index} after {bucket[-1].step_index}"
            )
        bucket.append(step)
        return step

    def record_thought(self, run_id: UUID, step_index: int, text: str) -> AgentStep:
        return self._append(run_id, step_index, "thought", {"text": text})

    def record_tool_call(
        self,
        run_id: UUID,
        step_index: int,
        tool_name: str,
        args: dict[str, Any],
    ) -> AgentStep:
        return self._append(
            run_id,
            step_index,
            "tool_call",
            {"args": args},
            tool_name=tool_name,
        )

    def record_tool_result(
        self,
        run_id: UUID,
        step_index: int,
        tool_name: str,
        result: dict[str, Any],
    ) -> AgentStep:
        return self._append(
            run_id,
            step_index,
            "tool_result",
            {"result": result},
            tool_name=tool_name,
        )

    def record_human_prompt(
        self,
        run_id: UUID,
        step_index: int,
        prompt: dict[str, Any],
    ) -> AgentStep:
        return self._append(run_id, step_index, "human_prompt", prompt)

    def record_human_response(
        self,
        run_id: UUID,
        step_index: int,
        response: dict[str, Any],
    ) -> AgentStep:
        return self._append(run_id, step_index, "human_response", response)

    def record_final(
        self,
        run_id: UUID,
        step_index: int,
        final: dict[str, Any],
    ) -> AgentStep:
        return self._append(run_id, step_index, "final", final)

    def list_steps(self, run_id: UUID) -> list[AgentStep]:
        return list(self._steps.get(str(run_id), []))


class SupabaseTraceRecorder:
    def __init__(self, repository: AgentStepsRepository) -> None:
        self._repository = repository

    def _append(
        self,
        run_id: UUID,
        step_index: int,
        step_type: AgentStepType,
        payload: dict[str, Any],
        tool_name: str | None = None,
    ) -> AgentStep:
        self._repository.append(
            run_id=run_id,
            step_index=step_index,
            step_type=step_type,
            payload=payload,
            tool_name=tool_name,
        )
        return AgentStep(
            run_id=run_id,
            step_index=step_index,
            step_type=step_type,
            tool_name=tool_name,
            payload=payload,
        )

    def record_thought(self, run_id: UUID, step_index: int, text: str) -> AgentStep:
        return self._append(run_id, step_index, "thought", {"text": text})

    def record_tool_call(
        self,
        run_id: UUID,
        step_index: int,
        tool_name: str,
        args: dict[str, Any],
    ) -> AgentStep:
        return self._append(
            run_id,
            step_index,
            "tool_call",
            {"args": args},
            tool_name=tool_name,
        )

    def record_tool_result(
        self,
        run_id: UUID,
        step_index: int,
        tool_name: str,
        result: dict[str, Any],
    ) -> AgentStep:
        return self._append(
            run_id,
            step_index,
            "tool_result",
            {"result": result},
            tool_name=tool_name,
        )

    def record_human_prompt(
        self,
        run_id: UUID,
        step_index: int,
        prompt: dict[str, Any],
    ) -> AgentStep:
        return self._append(run_id, step_index, "human_prompt", prompt)

    def record_human_response(
        self,
        run_id: UUID,
        step_index: int,
        response: dict[str, Any],
    ) -> AgentStep:
        return self._append(run_id, step_index, "human_response", response)

    def record_final(
        self,
        run_id: UUID,
        step_index: int,
        final: dict[str, Any],
    ) -> AgentStep:
        return self._append(run_id, step_index, "final", final)

    def list_steps(self, run_id: UUID) -> list[AgentStep]:
        rows = self._repository.list_for_run(run_id)
        return [
            AgentStep(
                run_id=run_id,
                step_index=int(row["step_index"]),
                step_type=row["step_type"],
                tool_name=row.get("tool_name"),
                payload=row.get("payload") or {},
            )
            for row in rows
        ]


def get_trace_recorder() -> TraceRecorder:
    return SupabaseTraceRecorder(get_agent_steps_repository())

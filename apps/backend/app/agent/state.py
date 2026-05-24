from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from app.schemas.agent import (
    AgentDecision,
    AgentFinal,
    AgentInitiator,
    AgentMode,
    AgentRunRequest,
    AgentRunStatus,
    HumanPrompt,
)


DEFAULT_MAX_ITERATIONS = 8
DEFAULT_DEADLINE_SECONDS = 60


@dataclass
class AgentTurn:
    role: str
    content: Any


@dataclass
class AgentState:
    run_id: UUID
    request: AgentRunRequest
    status: AgentRunStatus
    initiator: AgentInitiator
    iteration: int
    max_iterations: int
    started_at: datetime
    deadline: datetime
    transcript: list[AgentTurn] = field(default_factory=list)
    pending_human: HumanPrompt | None = None
    final: AgentFinal | None = None
    content_id: UUID | None = None
    model: str | None = None
    token_input: int = 0
    token_output: int = 0
    next_step_index: int = 0

    @property
    def user_message(self) -> str | None:
        if self.request.user_message:
            return self.request.user_message
        if self.request.text:
            return self.request.text
        return None

    @property
    def mode(self) -> AgentMode:
        return self.request.mode

    def claim_step_index(self) -> int:
        index = self.next_step_index
        self.next_step_index = index + 1
        return index

    def add_input_tokens(self, count: int) -> None:
        if count > 0:
            self.token_input += count

    def add_output_tokens(self, count: int) -> None:
        if count > 0:
            self.token_output += count

    def mark_decision(self, decision: AgentDecision, summary: str) -> None:
        if self.final is None:
            self.final = AgentFinal(decision=decision, summary=summary)
        else:
            self.final = self.final.model_copy(
                update={"decision": decision, "summary": summary or self.final.summary}
            )


def init_state(
    request: AgentRunRequest,
    *,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    deadline_seconds: int = DEFAULT_DEADLINE_SECONDS,
    model: str | None = None,
    now: datetime | None = None,
) -> AgentState:
    started_at = now or datetime.now(timezone.utc)
    return AgentState(
        run_id=uuid4(),
        request=request,
        status="running",
        initiator=request.initiator,
        iteration=0,
        max_iterations=max_iterations,
        started_at=started_at,
        deadline=started_at + timedelta(seconds=deadline_seconds),
        content_id=request.content_id,
        model=model,
    )


def time_exceeded(state: AgentState, *, now: datetime | None = None) -> bool:
    current = now or datetime.now(timezone.utc)
    return current >= state.deadline


def build_transcript(state: AgentState) -> list[AgentTurn]:
    """Day 17 agent runner will convert this into Gemini `contents`."""

    return list(state.transcript)

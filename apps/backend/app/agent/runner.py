import json
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from app.agent.fallback_runner import FALLBACK_MODEL_LABEL, FallbackAgentRunner
from app.agent.limits import AgentLimits, default_limits
from app.agent.state import AgentState, init_state, time_exceeded
from app.agent.tools import get_default_registry
from app.agent.tools.registry import ToolRegistry
from app.agent.trace import TraceRecorder, get_trace_recorder
from app.agent.transcript import SYSTEM_PROMPT, build_messages
from app.core.logging import get_logger
from app.integrations.llm import LlmProvider, get_llm_provider
from app.repositories.agent_runs_repo import (
    AgentRunsRepository,
    get_agent_runs_repository,
)
from app.schemas.agent import (
    AgentFinal,
    AgentRunDetail,
    AgentRunRequest,
    AgentStep,
    HumanPrompt,
)


logger = get_logger(__name__)


class AgentRunNotFoundError(LookupError):
    def __init__(self, run_id: str | UUID) -> None:
        super().__init__(f"Agent run {run_id} not found.")
        self.run_id = str(run_id)


class AgentRunStateError(RuntimeError):
    pass


class AgentRunner:
    def __init__(
        self,
        registry: ToolRegistry | None = None,
        llm_provider: LlmProvider | None = None,
        runs_repository: AgentRunsRepository | None = None,
        trace_recorder: TraceRecorder | None = None,
        limits: AgentLimits | None = None,
    ) -> None:
        self._registry = registry or get_default_registry()
        self._llm = llm_provider or get_llm_provider()
        self._runs_repository = runs_repository or get_agent_runs_repository()
        self._recorder = trace_recorder or get_trace_recorder()
        self._limits = limits or default_limits()
        self._fallback = FallbackAgentRunner(self._registry, self._recorder)

    # ----- entry points ---------------------------------------------------

    def run(self, request: AgentRunRequest) -> AgentRunDetail:
        state = init_state(
            request,
            max_iterations=self._limits.max_iterations,
            deadline_seconds=self._limits.deadline_seconds,
            model=(self._llm.model if self._llm.is_configured else FALLBACK_MODEL_LABEL),
        )

        self._runs_repository.insert(
            {
                "id": str(state.run_id),
                "content_id": str(state.content_id) if state.content_id else None,
                "status": "running",
                "initiator": request.initiator.value,
                "user_message": state.user_message,
                "model": state.model,
                "started_at": _utc_now_iso(),
            }
        )

        request_snapshot = json.dumps(request.model_dump(mode="json"), ensure_ascii=False)
        self._recorder.record_thought(
            state.run_id, state.claim_step_index(), "Starting compliance review."
        )
        # Persist a structured echo of the request inside the next step so
        # resume() can rebuild AgentRunRequest without a new column.
        self._recorder.record_thought(
            state.run_id,
            state.claim_step_index(),
            f"request_snapshot={request_snapshot}",
        )

        if not self._llm.is_configured:
            self._fallback.run_initial(state)
            return self._terminate(state)

        try:
            self._loop(state)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Agent run %s failed unexpectedly.", state.run_id)
            self._mark_failed(state, str(exc) or exc.__class__.__name__)
        return self._terminate(state)

    def resume(self, run_id: str | UUID, human_response: Any) -> AgentRunDetail:
        run_row = self._runs_repository.get(run_id)
        if run_row is None:
            raise AgentRunNotFoundError(run_id)
        if run_row.get("status") != "awaiting_human":
            raise AgentRunStateError(
                f"Cannot resume run {run_id}: status={run_row.get('status')!r}."
            )

        run_uuid = UUID(str(run_row.get("id") or run_id))
        existing_steps = self._recorder.list_steps(run_uuid)
        request = _request_from_steps(existing_steps)
        state = init_state(
            request,
            max_iterations=self._limits.max_iterations,
            deadline_seconds=self._limits.deadline_seconds,
            model=run_row.get("model"),
        )
        state.run_id = run_uuid
        state.next_step_index = (
            (existing_steps[-1].step_index + 1) if existing_steps else 0
        )
        # transcript can be reconstructed from steps; iteration starts fresh.
        state.iteration = 0

        self._recorder.record_human_response(
            state.run_id,
            state.claim_step_index(),
            {"response": _serialize_response(human_response)},
        )
        self._runs_repository.update(state.run_id, {"status": "running"})

        if not self._llm.is_configured:
            self._fallback.run_after_human_response(state, human_response)
            return self._terminate(state)

        try:
            self._loop(state)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Agent resume %s failed unexpectedly.", state.run_id)
            self._mark_failed(state, str(exc) or exc.__class__.__name__)
        return self._terminate(state)

    def cancel(self, run_id: str | UUID) -> AgentRunDetail:
        run_row = self._runs_repository.get(run_id)
        if run_row is None:
            raise AgentRunNotFoundError(run_id)
        if run_row.get("status") in {"done", "failed", "cancelled"}:
            return self.get(run_id)

        run_uuid = UUID(str(run_row.get("id") or run_id))
        steps = self._recorder.list_steps(run_uuid)
        next_index = (steps[-1].step_index + 1) if steps else 0
        self._recorder.record_final(
            run_uuid,
            next_index,
            {"decision": "none", "summary": "Cancelled by user."},
        )
        self._runs_repository.update(
            run_uuid,
            {
                "status": "cancelled",
                "final_decision": "none",
                "final_summary": "Cancelled by user.",
                "ended_at": _utc_now_iso(),
            },
        )
        return self.get(run_uuid)

    def get(self, run_id: str | UUID) -> AgentRunDetail:
        run_row = self._runs_repository.get(run_id)
        if run_row is None:
            raise AgentRunNotFoundError(run_id)

        run_uuid = UUID(str(run_row.get("id") or run_id))
        steps = self._recorder.list_steps(run_uuid)
        return _build_detail(run_uuid, run_row, steps)

    # ----- loop ----------------------------------------------------------

    def _loop(self, state: AgentState) -> None:
        while not state.final and not state.pending_human:
            if state.iteration >= state.max_iterations:
                self._mark_failed(state, "max_iterations_exceeded")
                return
            if time_exceeded(state):
                self._mark_failed(state, "deadline_exceeded")
                return

            existing_steps = self._recorder.list_steps(state.run_id)
            messages = build_messages(state.request, existing_steps)

            response = self._llm.generate_with_tools(
                messages=messages,
                function_declarations=self._registry.declarations(),
                system_instruction=SYSTEM_PROMPT,
            )

            if response is None:
                logger.warning("LLM returned no response; falling back to deterministic plan.")
                state.model = FALLBACK_MODEL_LABEL
                self._runs_repository.update(state.run_id, {"model": FALLBACK_MODEL_LABEL})
                human_response = _latest_human_response(existing_steps)
                if human_response is not None:
                    self._fallback.run_after_human_response(state, human_response)
                else:
                    self._fallback.run_initial(state)
                return

            state.add_input_tokens(response.input_tokens)
            state.add_output_tokens(response.output_tokens)

            if response.function_call is None:
                self._handle_text_only(state, response.text or "")
                return

            tool_name = response.function_call.name
            tool_args = response.function_call.args or {}
            self._recorder.record_tool_call(
                state.run_id, state.claim_step_index(), tool_name, dict(tool_args)
            )
            result_payload = self._registry.invoke(tool_name, tool_args, state)
            self._recorder.record_tool_result(
                state.run_id, state.claim_step_index(), tool_name, dict(result_payload)
            )

            state.iteration += 1

    def _handle_text_only(self, state: AgentState, text: str) -> None:
        # Model produced no tool call -> force a finalize_report call with decision=none.
        forced_args = {
            "content_id": (str(state.request.content_id) if state.request.content_id else "unknown"),
            "decision": "none",
            "summary": text.strip()[:500] or "Agent ended without explicit decision.",
        }
        self._recorder.record_tool_call(
            state.run_id, state.claim_step_index(), "finalize_report", forced_args
        )
        result_payload = self._registry.invoke("finalize_report", forced_args, state)
        self._recorder.record_tool_result(
            state.run_id, state.claim_step_index(), "finalize_report", dict(result_payload)
        )

    # ----- termination ----------------------------------------------------

    def _terminate(self, state: AgentState) -> AgentRunDetail:
        if state.pending_human:
            prompt = state.pending_human
            self._recorder.record_human_prompt(
                state.run_id,
                state.claim_step_index(),
                prompt.model_dump(mode="json"),
            )
            self._runs_repository.update(
                state.run_id,
                {
                    "status": "awaiting_human",
                    "token_input": state.token_input,
                    "token_output": state.token_output,
                },
            )
        elif state.final:
            self._recorder.record_final(
                state.run_id,
                state.claim_step_index(),
                state.final.model_dump(mode="json"),
            )
            # finalize_report already patched status/final_report; ensure the
            # token counters reach the persisted row as well.
            self._runs_repository.update(
                state.run_id,
                {
                    "token_input": state.token_input,
                    "token_output": state.token_output,
                    "ended_at": _utc_now_iso(),
                },
            )
        return self.get(state.run_id)

    def _mark_failed(self, state: AgentState, reason: str) -> None:
        summary = f"Agent run failed: {reason}"
        self._recorder.record_final(
            state.run_id,
            state.claim_step_index(),
            {"decision": "none", "summary": summary, "error": reason},
        )
        self._runs_repository.update(
            state.run_id,
            {
                "status": "failed",
                "final_decision": "none",
                "final_summary": summary,
                "ended_at": _utc_now_iso(),
                "token_input": state.token_input,
                "token_output": state.token_output,
            },
        )
        state.final = AgentFinal(decision="none", summary=summary)


# ----- helpers ----------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _build_detail(
    run_id: UUID,
    row: dict[str, Any],
    steps: list[AgentStep],
) -> AgentRunDetail:
    pending_human: HumanPrompt | None = None
    for step in reversed(steps):
        if step.step_type == "human_prompt":
            try:
                pending_human = HumanPrompt.model_validate(step.payload or {})
            except Exception:  # noqa: BLE001
                pending_human = None
            break
        if step.step_type in {"human_response", "final"}:
            break

    final_report = row.get("final_report")
    return AgentRunDetail(
        id=run_id,
        status=row.get("status", "running"),
        started_at=_parse_dt(row.get("started_at")) or datetime.now(timezone.utc),
        ended_at=_parse_dt(row.get("ended_at")),
        content_id=_parse_uuid(row.get("content_id")),
        initiator=row.get("initiator"),
        user_message=row.get("user_message"),
        final_decision=row.get("final_decision"),
        final_summary=row.get("final_summary"),
        token_input=row.get("token_input"),
        token_output=row.get("token_output"),
        model=row.get("model"),
        steps=steps,
        pending_human=pending_human if row.get("status") == "awaiting_human" else None,
        final_report=final_report if isinstance(final_report, dict) else None,
    )


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.replace("Z", "+00:00") if value.endswith("Z") else value
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None
    return None


def _parse_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _request_from_steps(steps: list[AgentStep]) -> AgentRunRequest:
    for step in steps:
        if step.step_type != "thought":
            continue
        text = (step.payload or {}).get("text", "") if isinstance(step.payload, dict) else ""
        if isinstance(text, str) and text.startswith("request_snapshot="):
            raw = text[len("request_snapshot="):]
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                logger.exception("Failed to JSON-decode request snapshot step.")
                continue
            if isinstance(payload, dict):
                try:
                    return AgentRunRequest.model_validate(payload)
                except Exception:  # noqa: BLE001
                    logger.exception("Failed to restore AgentRunRequest from snapshot step.")
    # Fall back to an empty review request; downstream tools may surface content_not_found.
    return AgentRunRequest(text="(resumed without original snapshot)")


def _serialize_response(human_response: Any) -> Any:
    if isinstance(human_response, (str, int, float, bool, type(None))):
        return human_response
    if isinstance(human_response, dict):
        return dict(human_response)
    if isinstance(human_response, list):
        return list(human_response)
    return str(human_response)


def _latest_human_response(steps: list[AgentStep]) -> Any:
    for step in reversed(steps):
        if step.step_type == "human_response":
            payload = step.payload if isinstance(step.payload, dict) else {}
            return payload.get("response")
    return None


def get_agent_runner() -> AgentRunner:
    return AgentRunner()


# Optional helper for the API layer to compute a deadline relative to a run start.
def deadline_from_started_at(started_at: datetime, deadline_seconds: int) -> datetime:
    return started_at + timedelta(seconds=deadline_seconds)

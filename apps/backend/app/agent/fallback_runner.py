from typing import Any

from app.agent.state import AgentState
from app.agent.tools.registry import ToolRegistry
from app.agent.trace import TraceRecorder


FALLBACK_MODEL_LABEL = "fallback-deterministic-agent"


class FallbackAgentRunner:
    """Deterministic four-step agent used when the LLM provider is unavailable.

    Step 1 (initial run): scan_rules.
    Step 2 (initial run): search_regulation if scan_rules surfaced any category.
    Step 3 (initial run): draft_rewrite if content_id is known.
    Step 4 (initial run): request_human_review -> pause.
    Step 5 (resume):      finalize_report.
    """

    def __init__(self, registry: ToolRegistry, recorder: TraceRecorder) -> None:
        self._registry = registry
        self._recorder = recorder

    def run_initial(self, state: AgentState) -> None:
        text = (state.request.text or state.request.user_message or "").strip()

        scan_result: dict[str, Any] = {}
        if text:
            scan_result = self._invoke("scan_rules", {"text": text}, state)
            if state.pending_human or state.final:
                return

        categories = list(scan_result.get("risk_categories") or [])
        if categories:
            product_type = state.request.product_type or "투자상품"
            self._invoke(
                "search_regulation",
                {
                    "risk_categories": categories,
                    "product_type": product_type,
                    "limit": 5,
                },
                state,
            )
            if state.pending_human or state.final:
                return

        if state.request.content_id is not None:
            self._invoke(
                "draft_rewrite",
                {
                    "content_id": str(state.request.content_id),
                    "mode": "marketing_balanced",
                },
                state,
            )
            if state.pending_human or state.final:
                return

        self._invoke(
            "request_human_review",
            {
                "question": "탐지된 위험 요소에 대해 어떻게 처리하시겠습니까?",
                "options": ["approve", "reject", "revise"],
                "proposed_action": {"decision": "revise"},
            },
            state,
        )

    def run_after_human_response(self, state: AgentState, human_response: Any) -> None:
        decision, selected_revision = _normalize_human_response(human_response)
        content_id = (
            str(state.request.content_id)
            if state.request.content_id is not None
            else _last_known_content_id(state, self._recorder) or "unknown"
        )

        self._invoke(
            "finalize_report",
            {
                "content_id": content_id,
                "decision": decision,
                "selected_revision": selected_revision,
                "reviewer": "AI Agent (fallback)",
                "summary": "",
            },
            state,
        )

    def _invoke(
        self,
        tool_name: str,
        args: dict[str, Any],
        state: AgentState,
    ) -> dict[str, Any]:
        call_index = state.claim_step_index()
        self._recorder.record_tool_call(state.run_id, call_index, tool_name, dict(args))
        result = self._registry.invoke(tool_name, args, state)
        result_index = state.claim_step_index()
        self._recorder.record_tool_result(state.run_id, result_index, tool_name, dict(result))
        return result


def _normalize_human_response(human_response: Any) -> tuple[str, str | None]:
    if isinstance(human_response, dict):
        raw_decision = str(human_response.get("decision") or "").strip().lower()
        selected = human_response.get("selected_revision")
    else:
        raw_decision = str(human_response or "").strip().lower()
        selected = None

    if raw_decision in {"approve", "reject", "revise", "none"}:
        decision = raw_decision
    elif raw_decision in {"approved", "accept"}:
        decision = "approve"
    elif raw_decision in {"rejected", "deny"}:
        decision = "reject"
    elif raw_decision in {"revision", "revision_requested"}:
        decision = "revise"
    else:
        decision = "none"

    return decision, (str(selected) if isinstance(selected, str) and selected else None)


def _last_known_content_id(state: AgentState, recorder: TraceRecorder) -> str | None:
    for step in reversed(recorder.list_steps(state.run_id)):
        if step.step_type != "tool_result":
            continue
        payload = step.payload or {}
        result = payload.get("result") if isinstance(payload, dict) else None
        if isinstance(result, dict) and isinstance(result.get("content_id"), str):
            return result["content_id"]
    return None

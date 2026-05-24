from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.agent import (
    AgentFinal,
    AgentInitiator,
    AgentRunDetail,
    AgentRunRequest,
    AgentRunResult,
    AgentStep,
    HumanPrompt,
    HumanResponse,
)
from app.schemas.tools import (
    DraftRewriteArgs,
    FetchContentArgs,
    FinalizeReportArgs,
    RequestHumanReviewArgs,
    ScanRulesArgs,
    SearchRegulationArgs,
    SearchRegulationHit,
)


def test_agent_run_request_minimum_payload() -> None:
    request = AgentRunRequest(text="누구나 안정적으로 받는 상품")

    assert request.mode == "review"
    assert request.initiator == AgentInitiator.USER
    assert request.language == "ko"
    assert request.content_id is None


def test_agent_run_request_rejects_invalid_mode() -> None:
    with pytest.raises(ValidationError):
        AgentRunRequest.model_validate({"mode": "free_form"})


def test_agent_step_index_must_be_non_negative() -> None:
    with pytest.raises(ValidationError):
        AgentStep(
            run_id=uuid4(),
            step_index=-1,
            step_type="thought",
            payload={"text": "bad"},
        )


def test_agent_step_round_trip() -> None:
    run_id = uuid4()
    step = AgentStep(
        run_id=run_id,
        step_index=2,
        step_type="tool_call",
        tool_name="scan_rules",
        payload={"args": {"text": "demo"}},
    )

    dumped = step.model_dump(mode="json")
    restored = AgentStep.model_validate(dumped)

    assert restored.step_type == "tool_call"
    assert restored.tool_name == "scan_rules"
    assert restored.payload["args"]["text"] == "demo"


def test_agent_run_detail_with_pending_human() -> None:
    run_id = uuid4()
    detail = AgentRunDetail(
        id=run_id,
        status="awaiting_human",
        started_at=datetime.now(timezone.utc),
        steps=[
            AgentStep(
                run_id=run_id,
                step_index=0,
                step_type="thought",
                payload={"text": "starting"},
            ),
            AgentStep(
                run_id=run_id,
                step_index=1,
                step_type="human_prompt",
                payload={
                    "question": "최종 결정이 필요합니다.",
                    "options": ["approve", "reject"],
                },
            ),
        ],
        pending_human=HumanPrompt(
            question="최종 결정이 필요합니다.",
            options=["approve", "reject"],
        ),
    )

    assert detail.status == "awaiting_human"
    assert detail.pending_human is not None
    assert detail.pending_human.options == ["approve", "reject"]
    assert len(detail.steps) == 2


def test_agent_run_result_serializes_to_json() -> None:
    run_id = uuid4()
    result = AgentRunResult(
        run=AgentRunDetail(
            id=run_id,
            status="done",
            started_at=datetime.now(timezone.utc),
            final_decision="approve",
            final_summary="ok",
        )
    )
    json_payload = result.model_dump_json()

    assert "done" in json_payload
    assert "approve" in json_payload


def test_human_response_accepts_text_or_dict() -> None:
    assert HumanResponse(response="approve").response == "approve"
    assert HumanResponse(response={"decision": "approve"}).response == {"decision": "approve"}


def test_agent_final_defaults() -> None:
    final = AgentFinal()
    assert final.decision == "none"
    assert final.selected_revision is None
    assert final.report is None


def test_tool_args_validation() -> None:
    FetchContentArgs(content_id="abc")
    ScanRulesArgs(text="누구나")
    SearchRegulationArgs(query="원금 보장", risk_categories=["원금 보장 오인"])
    DraftRewriteArgs(content_id="abc")
    RequestHumanReviewArgs(question="승인하시겠습니까?", options=["approve", "reject"])
    FinalizeReportArgs(content_id="abc", decision="approve", summary="done")


def test_search_regulation_hit_similarity_range() -> None:
    SearchRegulationHit(
        evidence_id="doc-1",
        title="가이드라인",
        version="v1",
        snippet="snippet",
        guideline_snippet="g",
        similarity=0.9,
    )
    with pytest.raises(ValidationError):
        SearchRegulationHit(
            evidence_id="doc-1",
            title="가이드라인",
            version="v1",
            snippet="snippet",
            guideline_snippet="g",
            similarity=1.5,
        )


def test_tool_args_reject_empty_strings() -> None:
    with pytest.raises(ValidationError):
        ScanRulesArgs(text="")
    with pytest.raises(ValidationError):
        FetchContentArgs(content_id="")
    with pytest.raises(ValidationError):
        RequestHumanReviewArgs(question="")


def test_search_regulation_args_clamps_limit() -> None:
    with pytest.raises(ValidationError):
        SearchRegulationArgs(limit=0)
    with pytest.raises(ValidationError):
        SearchRegulationArgs(limit=21)

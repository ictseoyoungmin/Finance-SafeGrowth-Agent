import json
from typing import Any, Iterator
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.agent.runner import (
    AgentRunNotFoundError,
    AgentRunStateError,
    AgentRunner,
    get_agent_runner,
)
from app.schemas.agent import (
    AgentRunDetail,
    AgentRunRequest,
    HumanResponse,
)


router = APIRouter(tags=["agent"])


@router.post("/run", response_model=AgentRunDetail)
def start_agent_run(
    request: AgentRunRequest,
    runner: AgentRunner = Depends(get_agent_runner),
) -> AgentRunDetail:
    return runner.run(request)


@router.get("/runs/{run_id}", response_model=AgentRunDetail)
def get_agent_run(
    run_id: UUID,
    runner: AgentRunner = Depends(get_agent_runner),
) -> AgentRunDetail:
    try:
        return runner.get(run_id)
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/runs/{run_id}/respond", response_model=AgentRunDetail)
def respond_to_agent_run(
    run_id: UUID,
    payload: HumanResponse,
    runner: AgentRunner = Depends(get_agent_runner),
) -> AgentRunDetail:
    try:
        return runner.resume(run_id, payload.response)
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AgentRunStateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/runs/{run_id}/cancel", response_model=AgentRunDetail)
def cancel_agent_run(
    run_id: UUID,
    runner: AgentRunner = Depends(get_agent_runner),
) -> AgentRunDetail:
    try:
        return runner.cancel(run_id)
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/runs/{run_id}/stream")
def stream_agent_run(
    run_id: UUID,
    runner: AgentRunner = Depends(get_agent_runner),
) -> StreamingResponse:
    try:
        detail = runner.get(run_id)
    except AgentRunNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    def _iter() -> Iterator[bytes]:
        for step in detail.steps:
            yield _sse_event("step", step.model_dump(mode="json"))
        yield _sse_event(
            "status",
            {
                "id": str(detail.id),
                "status": detail.status,
                "final_decision": detail.final_decision,
                "final_summary": detail.final_summary,
            },
        )
        yield _sse_comment("end-of-trace")

    return StreamingResponse(_iter(), media_type="text/event-stream")


def _sse_event(event: str, data: Any) -> bytes:
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n".encode("utf-8")


def _sse_comment(text: str) -> bytes:
    return f": {text}\n\n".encode("utf-8")

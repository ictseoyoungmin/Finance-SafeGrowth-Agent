import { replaceApprovalDecisionCodes } from "../../compliance/approvalDecisionLabels";
import type { AgentStep } from "../types";

interface StepDetailPanelProps {
  step?: AgentStep;
}

export function StepDetailPanel({ step }: StepDetailPanelProps) {
  if (!step) {
    return (
      <section className="step-detail-panel">
        <h2>상세 정보</h2>
        <p>Trace 항목을 선택하면 도구 입력과 결과가 표시됩니다.</p>
      </section>
    );
  }

  return (
    <section className="step-detail-panel">
      <div className="panel-heading compact">
        <div>
          <h2>{step.tool_name ?? stepTypeLabel(step.step_type)}</h2>
          <p>{friendlySummary(step)}</p>
        </div>
        <span className={`run-pill step-${step.step_type}`}>{stepTypeLabel(step.step_type)} #{step.step_index}</span>
      </div>
      <FriendlyPayload step={step} />
      <details className="json-details">
        <summary>원본 JSON</summary>
        <pre>{JSON.stringify(step.payload, null, 2)}</pre>
      </details>
    </section>
  );
}

function FriendlyPayload({ step }: { step: AgentStep }) {
  const payload = step.payload ?? {};
  const args = payload.args as Record<string, unknown> | undefined;
  const result = (payload.result ?? payload.output ?? payload) as Record<string, unknown> | undefined;

  if (step.tool_name === "scan_rules" && step.step_type === "tool_result" && result) {
    const spans = (result.flagged_spans as Array<Record<string, unknown>> | undefined) ?? [];
    return (
      <div className="agent-summary-grid">
        <span><strong>{String(result.risk_level ?? "-")}</strong>리스크 수준</span>
        <span><strong>{spans.length}</strong>탐지 표현</span>
        <div className="agent-chip-row">
          {spans.map((span, index) => (
            <i key={`${String(span.span_text)}-${index}`}>{index + 1}. {String(span.span_text)}</i>
          ))}
        </div>
      </div>
    );
  }

  if (isRegulationSearch(step.tool_name) && step.step_type === "tool_result" && result) {
    const evidence =
      (result.evidence as Array<Record<string, unknown>> | undefined) ??
      (result.evidence_list as Array<Record<string, unknown>> | undefined) ??
      [];
    return (
      <div className="agent-evidence-mini">
        {evidence.map((item, index) => (
          <article key={`${String(item.evidence_id)}-${index}`}>
            <strong>근거 {index + 1}</strong>
            <p>{String(item.title ?? "규정 문서")} · 관련도 {Math.round(Number(item.similarity ?? 0) * 100)}%</p>
            <small>{String(item.guideline_snippet ?? item.snippet ?? "")}</small>
          </article>
        ))}
      </div>
    );
  }

  if (isRewriteTool(step.tool_name) && step.step_type === "tool_result" && result) {
    const changes = (result.changes as Array<Record<string, unknown>> | undefined) ?? [];
    return (
      <div className="agent-summary-grid">
        <span><strong>{changes.length}</strong>수정 포인트</span>
        <span><strong>{String(result.source ?? "agent")}</strong>생성 경로</span>
        <div className="agent-chip-row">
          {changes.map((change, index) => (
            <i key={`${String(change.original)}-${index}`}>{index + 1}. {String(change.replacement ?? change.original)}</i>
          ))}
        </div>
      </div>
    );
  }

  if (step.step_type === "tool_call" && args) {
    return (
      <p className="agent-plain-summary">
        {step.tool_name ?? "도구"} 실행을 위해 {Object.keys(args).length}개 입력 인자를 전달했습니다.
      </p>
    );
  }

  if (step.step_type === "human_prompt") {
    const question = payload.question ?? payload.prompt ?? payload.message;
    return (
      <p className="agent-plain-summary">
        {replaceApprovalDecisionCodes(String(question ?? "사람의 최종 확인을 요청했습니다."))}
      </p>
    );
  }

  if (step.step_type === "final") {
    const summary = payload.summary ?? payload.final_summary ?? payload.message;
    return (
      <p className="agent-plain-summary">
        {replaceApprovalDecisionCodes(String(summary ?? "Agent 실행이 완료되었습니다."))}
      </p>
    );
  }

  return <p className="agent-plain-summary">이 단계는 상태 기록 또는 최종 결과입니다.</p>;
}

function friendlySummary(step: AgentStep) {
  if (step.step_type === "tool_call") return "Agent가 다음 도구 실행을 선택했습니다.";
  if (step.step_type === "tool_result") return "도구 실행 결과가 trace에 저장되었습니다.";
  if (step.step_type === "human_prompt") return "사람의 판단이 필요한 지점입니다.";
  if (step.step_type === "final") return "Agent 실행이 종료되었습니다.";
  return "Agent 실행 중 기록된 판단 흐름입니다.";
}

function isRegulationSearch(toolName?: string | null) {
  return toolName === "search_regulation" || toolName === "search_regulations";
}

function isRewriteTool(toolName?: string | null) {
  return toolName === "draft_rewrite" || toolName === "rewrite_content";
}

function stepTypeLabel(type: string) {
  const labels: Record<string, string> = {
    thought: "생각",
    tool_call: "도구 호출",
    tool_result: "도구 결과",
    human_prompt: "사람 검토 요청",
    human_response: "사람 응답",
    final: "최종 결과",
  };
  return labels[type] ?? type;
}

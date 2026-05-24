import { replaceApprovalDecisionCodes } from "../../compliance/approvalDecisionLabels";
import {
  findPairedToolCall,
  getArgs,
  getEvidence,
  getResult,
  isRegulationSearch,
  isRewriteTool,
  thoughtSummary,
  toolLabel,
  toolReason,
  traceSubtitle,
  traceTitle,
  traceTypeLabel,
} from "../tracePresentation";
import type { AgentStep } from "../types";

interface StepDetailPanelProps {
  step?: AgentStep;
  steps?: AgentStep[];
}

export function StepDetailPanel({ step, steps = [] }: StepDetailPanelProps) {
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
          <h2>{traceTitle(step)}</h2>
          <p>{traceSubtitle(step)}</p>
        </div>
        <span className={`run-pill step-${step.step_type}`}>{traceTypeLabel(step.step_type)} #{step.step_index}</span>
      </div>
      <FriendlyPayload step={step} steps={steps} />
      <details className="json-details">
        <summary>원본 JSON</summary>
        <pre>{JSON.stringify(step.payload, null, 2)}</pre>
      </details>
    </section>
  );
}

function FriendlyPayload({ step, steps }: { step: AgentStep; steps: AgentStep[] }) {
  const payload = step.payload ?? {};
  const args = getArgs(step);
  const result = getResult(step);
  const pairedCall = findPairedToolCall(step, steps);
  const pairedArgs = pairedCall ? getArgs(pairedCall) : {};

  if (step.step_type === "thought") {
    return (
      <div className="agent-trace-explain">
        <strong>생각 파싱</strong>
        <p>{thoughtSummary(step)}</p>
      </div>
    );
  }

  if (step.tool_name === "scan_rules" && step.step_type === "tool_result" && result) {
    const spans = (result.flagged_spans as Array<Record<string, unknown>> | undefined) ?? [];
    return (
      <div className="agent-tool-card">
        <ToolHeader toolName={step.tool_name} args={pairedArgs} />
        <div className="agent-summary-grid">
          <span><strong>{String(result.risk_level ?? "-")}</strong>리스크 수준</span>
          <span><strong>{spans.length}</strong>탐지 표현</span>
        </div>
        <div className="agent-chip-row">
          {spans.map((span, index) => (
            <i key={`${String(span.span_text)}-${index}`}>
              {index + 1}. {String(span.span_text)} · {String(span.risk_category ?? "risk")}
            </i>
          ))}
        </div>
      </div>
    );
  }

  if (isRegulationSearch(step.tool_name) && step.step_type === "tool_result" && result) {
    const evidence = getEvidence(result);
    return (
      <div className="agent-tool-card">
        <ToolHeader toolName={step.tool_name} args={pairedArgs} />
        <div className="agent-rag-summary">
          <span>검색 카테고리</span>
          <strong>{formatArgList(pairedArgs.risk_categories)}</strong>
          <span>상품 유형</span>
          <strong>{String(pairedArgs.product_type ?? "-")}</strong>
        </div>
        <div className="agent-evidence-mini">
        {evidence.map((item, index) => (
          <article key={`${String(item.evidence_id)}-${index}`}>
            <strong>근거 {index + 1}</strong>
            <p>{String(item.title ?? "규정 문서")} · 관련도 {Math.round(Number(item.similarity ?? 0) * 100)}%</p>
            <small>{String(item.guideline_snippet ?? item.snippet ?? "")}</small>
          </article>
        ))}
        </div>
      </div>
    );
  }

  if (isRewriteTool(step.tool_name) && step.step_type === "tool_result" && result) {
    const changes = (result.changes as Array<Record<string, unknown>> | undefined) ?? [];
    return (
      <div className="agent-tool-card">
        <ToolHeader toolName={step.tool_name} args={pairedArgs} />
        <div className="agent-summary-grid">
          <span><strong>{changes.length}</strong>수정 포인트</span>
          <span><strong>{String(result.source ?? "agent")}</strong>생성 경로</span>
        </div>
        <div className="agent-chip-row">
          {changes.map((change, index) => (
            <i key={`${String(change.original)}-${index}`}>{index + 1}. {String(change.replacement ?? change.original)}</i>
          ))}
        </div>
      </div>
    );
  }

  if (step.step_type === "tool_call") {
    return (
      <div className="agent-tool-card">
        <ToolHeader toolName={step.tool_name} args={args} />
      </div>
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

  if (step.step_type === "tool_result" && step.tool_name) {
    return (
      <div className="agent-tool-card">
        <ToolHeader toolName={step.tool_name} args={pairedArgs} />
        <p className="agent-plain-summary">{traceSubtitle(step)}</p>
      </div>
    );
  }

  return <p className="agent-plain-summary">이 단계는 상태 기록 또는 최종 결과입니다.</p>;
}

function ToolHeader({ toolName, args }: { toolName?: string | null; args: Record<string, unknown> }) {
  return (
    <div className="agent-tool-header">
      <div>
        <span>실제 함수</span>
        <strong>{toolName ?? "-"}</strong>
        <small>{toolLabel(toolName)}</small>
      </div>
      <div>
        <span>사용 이유</span>
        <p>{toolReason(toolName)}</p>
      </div>
      <div>
        <span>입력</span>
        <p>{summarizeArgs(args)}</p>
      </div>
    </div>
  );
}

function summarizeArgs(args: Record<string, unknown>) {
  if (!Object.keys(args).length) return "입력 인자 없음";
  if (args.risk_categories) return `risk_categories=${formatArgList(args.risk_categories)}, product_type=${String(args.product_type ?? "-")}`;
  if (args.text) return `text ${String(args.text).length}자`;
  if (args.content_id) return `content_id=${String(args.content_id)}, mode=${String(args.mode ?? "-")}`;
  if (args.question) return String(args.question);
  if (args.decision) return `decision=${replaceApprovalDecisionCodes(String(args.decision))}`;
  return `${Object.keys(args).length}개 인자`;
}

function formatArgList(value: unknown) {
  return Array.isArray(value) ? value.map(String).join(", ") : String(value ?? "-");
}

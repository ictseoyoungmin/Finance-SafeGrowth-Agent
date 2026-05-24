import { replaceApprovalDecisionCodes } from "../compliance/approvalDecisionLabels";
import type { AgentStep } from "./types";

export function traceTypeLabel(type: string) {
  const labels: Record<string, string> = {
    thought: "생각",
    tool_call: "도구 호출",
    tool_result: "도구 결과",
    human_prompt: "사람 확인 요청",
    human_response: "사람 응답",
    final: "최종 결과",
  };
  return labels[type] ?? type;
}

export function toolLabel(toolName?: string | null) {
  const labels: Record<string, string> = {
    fetch_content: "콘텐츠 불러오기",
    scan_rules: "규칙 스캔",
    search_regulation: "RAG 근거 검색",
    draft_rewrite: "수정안 생성",
    request_human_review: "사람 확인 요청",
    finalize_report: "리포트 확정",
  };
  return toolName ? labels[toolName] ?? toolName : "";
}

export function toolReason(toolName?: string | null) {
  const reasons: Record<string, string> = {
    fetch_content: "저장된 콘텐츠 원문과 문맥을 먼저 확보하기 위해 사용했습니다.",
    scan_rules: "수익률, 원금, 확정 표현 같은 금융 광고 리스크를 빠르게 탐지하기 위해 사용했습니다.",
    search_regulation: "탐지된 리스크 카테고리에 맞는 내부 규정과 가이드라인 근거를 찾기 위해 사용했습니다.",
    draft_rewrite: "리스크 표현을 완화하면서 마케팅 문맥을 유지한 대체 문안을 만들기 위해 사용했습니다.",
    request_human_review: "규제 판단은 자동 확정하지 않고 담당자의 결정을 받기 위해 사용했습니다.",
    finalize_report: "사람의 응답을 승인 기록과 최종 리포트로 묶기 위해 사용했습니다.",
  };
  return toolName ? reasons[toolName] ?? "Agent가 다음 판단에 필요한 도구로 선택했습니다." : "";
}

export function traceTitle(step: AgentStep) {
  if (step.tool_name) return toolLabel(step.tool_name);
  if (step.step_type === "thought") return thoughtTitle(step);
  return traceTypeLabel(step.step_type);
}

export function traceSubtitle(step: AgentStep) {
  if (step.step_type === "tool_call") return toolReason(step.tool_name);
  if (step.step_type === "tool_result") return resultSummary(step);
  if (step.step_type === "thought") return thoughtSummary(step);
  if (step.step_type === "human_prompt") return "검토자가 선택할 수 있는 판단 지점을 만들었습니다.";
  if (step.step_type === "human_response") return "검토자의 응답을 trace에 기록했습니다.";
  if (step.step_type === "final") return replaceApprovalDecisionCodes(String(step.payload.summary ?? step.payload.message ?? "실행을 마쳤습니다."));
  return "Agent 실행 기록입니다.";
}

export function resultSummary(step: AgentStep) {
  const result = getResult(step);
  if (step.tool_name === "scan_rules") {
    const spans = arrayOfRecords(result.flagged_spans);
    return `${String(result.risk_level ?? "-")} · 탐지 표현 ${spans.length}건`;
  }
  if (isRegulationSearch(step.tool_name)) {
    const evidence = getEvidence(result);
    return `RAG 근거 ${evidence.length}건 사용`;
  }
  if (step.tool_name === "draft_rewrite") {
    const changes = arrayOfRecords(result.changes);
    return `수정 포인트 ${changes.length}건 · ${String(result.source ?? "agent")}`;
  }
  if (step.tool_name === "request_human_review") return "사람 승인 단계로 일시 중지";
  if (step.tool_name === "finalize_report") return replaceApprovalDecisionCodes(String(result.summary ?? "최종 리포트 생성"));
  return "도구 실행 결과를 받았습니다.";
}

export function getArgs(step: AgentStep) {
  return (step.payload.args as Record<string, unknown> | undefined) ?? {};
}

export function getResult(step: AgentStep) {
  return (step.payload.result ?? step.payload.output ?? step.payload) as Record<string, unknown>;
}

export function getEvidence(result: Record<string, unknown>) {
  const evidence = arrayOfRecords(result.evidence);
  return evidence.length ? evidence : arrayOfRecords(result.evidence_list);
}

export function findPairedToolCall(step: AgentStep, steps: AgentStep[]) {
  if (step.step_type !== "tool_result") return undefined;
  return [...steps]
    .reverse()
    .find(
      (candidate) =>
        candidate.step_type === "tool_call" &&
        candidate.tool_name === step.tool_name &&
        candidate.step_index < step.step_index,
    );
}

export function isRegulationSearch(toolName?: string | null) {
  return toolName === "search_regulation" || toolName === "search_regulations";
}

export function isRewriteTool(toolName?: string | null) {
  return toolName === "draft_rewrite" || toolName === "rewrite_content";
}

export function thoughtSummary(step: AgentStep) {
  const text = String(step.payload.text ?? "");
  if (text.startsWith("request_snapshot=")) {
    const request = parseRequestSnapshot(text);
    if (request) {
      return `${String(request.product_type ?? "상품")} · ${String(request.channel ?? "채널")} · ${String(request.target_customer ?? "대상 고객")}`;
    }
  }
  if (text === "Starting compliance review.") return "검토 실행을 시작했습니다.";
  return replaceApprovalDecisionCodes(text || "Agent 판단 기록입니다.");
}

function thoughtTitle(step: AgentStep) {
  const text = String(step.payload.text ?? "");
  if (text.startsWith("request_snapshot=")) return "요청 문맥 파싱";
  if (text === "Starting compliance review.") return "실행 시작";
  return "생각 기록";
}

function parseRequestSnapshot(text: string) {
  try {
    return JSON.parse(text.replace(/^request_snapshot=/, "")) as Record<string, unknown>;
  } catch {
    return undefined;
  }
}

function arrayOfRecords(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object") : [];
}

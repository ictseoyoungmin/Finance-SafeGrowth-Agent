import { useState } from "react";

import { approvalDecisionLabel } from "../approvalDecisionLabels";
import { riskCategoryKo, riskReasonKo } from "../riskPresentation";
import type { ComplianceWorkflow } from "../store";
import type { WorkflowStep } from "../types";

interface ComplianceTraceRailProps {
  workflow: ComplianceWorkflow;
}

interface TraceItem {
  id: WorkflowStep;
  label: string;
  status: "done" | "active" | "pending";
  detail: string;
  meta: Array<{ label: string; value: string }>;
}

interface JudgmentItem {
  id: string;
  label: string;
  status: "done" | "active" | "pending";
  observation: string;
  decision: string;
  nextAction: string;
}

const STEP_ORDER: WorkflowStep[] = ["input", "redline", "evidence", "rewrite", "approval"];

export function ComplianceTraceRail({ workflow }: ComplianceTraceRailProps) {
  const { state, goTo } = workflow;
  const items = buildTraceItems(workflow);
  const judgments = buildJudgmentItems(workflow);
  const currentItem = items.find((item) => item.id === state.step) ?? items[0];
  const currentJudgment =
    judgments.find((item) => item.status === "active") ??
    lastDoneJudgment(judgments) ??
    judgments[0];
  const [selectedId, setSelectedId] = useState<WorkflowStep | undefined>();
  const [selectedJudgmentId, setSelectedJudgmentId] = useState<string | undefined>();
  const selected = items.find((item) => item.id === selectedId) ?? currentItem;
  const selectedJudgment =
    judgments.find((item) => item.id === selectedJudgmentId) ?? currentJudgment;

  return (
    <aside className="compliance-trace-rail" aria-label="검토 trace와 상세 정보">
      <section className="trace-rail-card">
        <div className="panel-heading compact">
          <div>
            <h2>검토 흐름</h2>
            <p>5-step 진행 상태</p>
          </div>
          <span className={`run-pill trace-${currentItem.status}`}>{statusLabel(currentItem.status)}</span>
        </div>
        <div className="legacy-trace-list">
          {items.map((item, index) => (
            <button
              key={item.id}
              className={`legacy-trace-item is-${item.status} ${selected.id === item.id ? "is-selected" : ""}`}
              onClick={() => {
                setSelectedId(item.id);
                if (item.status !== "pending") goTo(item.id);
              }}
            >
              <span>{index + 1}</span>
              <div>
                <strong>{item.label}</strong>
                <small>{item.detail}</small>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="trace-rail-card agent-judgment-card">
        <div className="panel-heading compact">
          <div>
            <h2>Agent 판단 흐름</h2>
            <p>관찰 → 판단 → 다음 행동</p>
          </div>
        </div>
        <div className="agent-judgment-list">
          {judgments.map((item, index) => (
            <button
              key={item.id}
              className={`agent-judgment-item is-${item.status} ${
                selectedJudgment.id === item.id ? "is-selected" : ""
              }`}
              onClick={() => setSelectedJudgmentId(item.id)}
            >
              <span>{index + 1}</span>
              <div>
                <strong>{item.label}</strong>
                <small>{item.decision}</small>
              </div>
            </button>
          ))}
        </div>
      </section>

      <section className="trace-rail-card detail">
        <div className="panel-heading compact">
          <div>
            <h2>상세 정보</h2>
            <p>{selected.label}</p>
          </div>
        </div>
        <p className="trace-detail-copy">{selected.detail}</p>
        <div className="trace-meta-grid">
          {selected.meta.map((item) => (
            <span key={item.label}>
              <strong>{item.value}</strong>
              {item.label}
            </span>
          ))}
        </div>
      </section>

      <section className="trace-rail-card judgment-detail">
        <div className="panel-heading compact">
          <div>
            <h2>판단 상세</h2>
            <p>{selectedJudgment.label}</p>
          </div>
          <span className={`run-pill trace-${selectedJudgment.status}`}>
            {statusLabel(selectedJudgment.status)}
          </span>
        </div>
        <dl className="judgment-detail-list">
          <div>
            <dt>관찰</dt>
            <dd>{selectedJudgment.observation}</dd>
          </div>
          <div>
            <dt>판단</dt>
            <dd>{selectedJudgment.decision}</dd>
          </div>
          <div>
            <dt>다음 행동</dt>
            <dd>{selectedJudgment.nextAction}</dd>
          </div>
        </dl>
      </section>
    </aside>
  );
}

function buildTraceItems(workflow: ComplianceWorkflow): TraceItem[] {
  const { state } = workflow;
  const currentIndex = STEP_ORDER.indexOf(state.step);
  const riskCount = state.analyze?.flagged_spans.length ?? 0;
  const evidenceCount = state.evidence?.evidence_list.length ?? 0;
  const rewriteCount = state.rewrite?.changes.length ?? 0;

  return [
    {
      id: "input",
      label: "콘텐츠 입력",
      status: statusFor(0, currentIndex),
      detail: `${state.input.product_type} · ${state.input.channel} · ${state.input.target_customer}`,
      meta: [
        { label: "문자 수", value: String(state.input.original_text.length) },
        { label: "언어", value: state.input.language.toUpperCase() },
      ],
    },
    {
      id: "redline",
      label: "리스크 분석",
      status: state.analyze ? statusFor(1, currentIndex) : "pending",
      detail: state.analyze
        ? `${state.analyze.risk_level} · 탐지 표현 ${riskCount}건`
        : "준법 리스크 분석 대기",
      meta: [
        { label: "위험도", value: state.analyze?.risk_level ?? "-" },
        { label: "탐지", value: String(riskCount) },
      ],
    },
    {
      id: "evidence",
      label: "근거 매칭",
      status: state.evidence ? statusFor(2, currentIndex) : "pending",
      detail: state.evidence ? `참조 근거 ${evidenceCount}건 연결` : "규정·가이드라인 검색 대기",
      meta: [
        { label: "근거", value: String(evidenceCount) },
        { label: "리스크", value: String(state.analyze?.risk_categories.length ?? 0) },
      ],
    },
    {
      id: "rewrite",
      label: "수정안 생성",
      status: state.rewrite ? statusFor(3, currentIndex) : "pending",
      detail: state.rewrite ? `변경 포인트 ${rewriteCount}건 · ${state.rewrite.source ?? "llm"}` : "문구 수정안 생성 대기",
      meta: [
        { label: "변경", value: String(rewriteCount) },
        { label: "선택안", value: state.selectedRevision === "marketing" ? "마케팅" : "보수" },
      ],
    },
    {
      id: "approval",
      label: "승인 패키지",
      status: state.approval || state.step === "approval" ? statusFor(4, currentIndex) : "pending",
      detail: state.approval
        ? `심의 결과 ${approvalDecisionLabel(state.approval.decision)}`
        : "최종 승인 및 리포트 확인",
      meta: [
        { label: "결정", value: state.approval ? approvalDecisionLabel(state.approval.decision) : "-" },
        { label: "리포트", value: state.report ? "완료" : "대기" },
      ],
    },
  ];
}

function buildJudgmentItems(workflow: ComplianceWorkflow): JudgmentItem[] {
  const { state } = workflow;
  const riskCount = state.analyze?.flagged_spans.length ?? 0;
  const topRisk = state.analyze?.flagged_spans[0];
  const evidenceCount = state.evidence?.evidence_list.length ?? 0;
  const rewriteCount = state.rewrite?.changes.length ?? 0;
  const approvalDecision = state.approval?.decision;
  const approvalLabel = approvalDecisionLabel(approvalDecision);

  return [
    {
      id: "context",
      label: "문맥 구성",
      status: state.step === "input" ? "active" : "done",
      observation: `${state.input.product_type}, ${state.input.channel}, ${state.input.target_customer} 조건의 광고 문안입니다.`,
      decision: "상품·채널·대상 고객을 함께 묶어 심사 문맥을 구성합니다.",
      nextAction: "수익률, 원금, 안전성 표현을 우선 스캔합니다.",
    },
    {
      id: "risk-scan",
      label: "위험 요소 판단",
      status: state.analyze ? (state.step === "redline" ? "active" : "done") : "pending",
      observation: topRisk
        ? `${topRisk.span_text} 표현에서 ${riskCategoryKo(topRisk.risk_category)} 신호가 감지되었습니다.`
        : "아직 분석 결과가 없습니다.",
      decision: state.analyze
        ? `${state.analyze.risk_level} 수준으로 보고, ${riskCount}개 표현을 사람 검토 대상으로 올립니다.`
        : "탐지 결과를 기다립니다.",
      nextAction: topRisk ? riskReasonKo(topRisk) : "리스크 분석을 먼저 실행합니다.",
    },
    {
      id: "evidence-search",
      label: "근거 선택",
      status: state.evidence ? (state.step === "evidence" ? "active" : "done") : "pending",
      observation: state.analyze?.risk_categories.length
        ? `${state.analyze.risk_categories.map(riskCategoryKo).join(", ")} 카테고리를 검색 키로 사용합니다.`
        : "검색할 리스크 카테고리가 아직 없습니다.",
      decision: state.evidence
        ? `관련도 높은 내부 규정 ${evidenceCount}건을 판단 근거로 연결합니다.`
        : "리스크 카테고리가 확정되면 근거 검색을 실행합니다.",
      nextAction: state.evidence ? "근거와 대응 문장을 번호로 매칭해 검토자가 추적하도록 합니다." : "근거 패널로 이동합니다.",
    },
    {
      id: "rewrite-strategy",
      label: "수정 전략",
      status: state.rewrite ? (state.step === "rewrite" ? "active" : "done") : "pending",
      observation: state.rewrite
        ? `${rewriteCount}개 변경 포인트와 ${state.selectedRevision === "marketing" ? "마케팅 균형안" : "보수안"}이 준비되었습니다.`
        : "아직 수정안이 생성되지 않았습니다.",
      decision: state.rewrite
        ? "위험 표현은 완화하고 상품 매력도는 유지하는 방향을 선택합니다."
        : "근거 확인 후 수정 전략을 결정합니다.",
      nextAction: "최종 승인 전에 사람이 선택안을 확인합니다.",
    },
    {
      id: "human-escalation",
      label: "사람 판단 요청",
      status: approvalDecision ? "done" : state.step === "approval" ? "active" : "pending",
      observation: approvalDecision
        ? `심의 결과가 ${approvalLabel}으로 기록되었습니다.`
        : "최종 문안과 근거가 준비되면 사람 승인 단계로 넘깁니다.",
      decision: approvalDecision
        ? "사람의 최종 판단을 감사 기록과 리포트에 반영합니다."
        : "규제 리스크가 있는 문구는 자동 승인하지 않고 준법 담당자에게 결정을 요청합니다.",
      nextAction: approvalDecision ? "리포트 패키지를 확인합니다." : "승인, 반려, 수정 요청 중 하나를 선택합니다.",
    },
  ];
}

function lastDoneJudgment(items: JudgmentItem[]) {
  const doneItems = items.filter((item) => item.status === "done");
  return doneItems[doneItems.length - 1];
}

function statusFor(index: number, currentIndex: number): TraceItem["status"] {
  if (index < currentIndex) return "done";
  if (index === currentIndex) return "active";
  return "pending";
}

function statusLabel(status: TraceItem["status"]) {
  if (status === "done") return "완료";
  if (status === "active") return "진행 중";
  return "대기";
}

import { useState } from "react";

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

const STEP_ORDER: WorkflowStep[] = ["input", "redline", "evidence", "rewrite", "approval"];

export function ComplianceTraceRail({ workflow }: ComplianceTraceRailProps) {
  const { state, goTo } = workflow;
  const items = buildTraceItems(workflow);
  const currentItem = items.find((item) => item.id === state.step) ?? items[0];
  const [selectedId, setSelectedId] = useState<WorkflowStep | undefined>();
  const selected = items.find((item) => item.id === selectedId) ?? currentItem;

  return (
    <aside className="compliance-trace-rail" aria-label="검토 trace와 상세 정보">
      <section className="trace-rail-card">
        <div className="panel-heading compact">
          <div>
            <h2>Trace</h2>
            <p>현재 검토 흐름</p>
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
      detail: state.approval ? `심의 결과 ${state.approval.decision}` : "최종 승인 및 리포트 확인",
      meta: [
        { label: "결정", value: state.approval?.decision ?? "-" },
        { label: "리포트", value: state.report ? "완료" : "대기" },
      ],
    },
  ];
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

import { useMemo, useState } from "react";

import { renderRedline } from "../../../components/redline/renderRedline";
import { riskCategoryKo, riskReasonKo, sourceLabel } from "../riskPresentation";
import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function RedlineStep({ workflow }: StepProps) {
  const { state, loadEvidence, goTo } = workflow;
  const analyze = state.analyze;
  const [riskPage, setRiskPage] = useState(0);
  const flaggedSpans = useMemo(() => analyze?.flagged_spans ?? [], [analyze?.flagged_spans]);
  const safePage = flaggedSpans.length ? Math.min(riskPage, flaggedSpans.length - 1) : 0;
  const activeSpan = flaggedSpans[safePage];
  const categoryList = useMemo(
    () => Array.from(new Set(flaggedSpans.map((span) => span.risk_category))),
    [flaggedSpans],
  );

  if (!analyze) {
    return null;
  }

  const confidence =
    analyze.flagged_spans.length > 0
      ? Math.round(
          (analyze.flagged_spans.reduce((sum, span) => sum + span.confidence, 0) /
            analyze.flagged_spans.length) *
            100,
        )
      : 0;

  return (
    <div className="review-layout">
      <section className="document-panel">
        <div className="panel-heading compact">
          <div>
            <h2>검토된 문장</h2>
            <p>위험 표현이 감지된 구간을 확인하세요.</p>
          </div>
          <button className="ghost-button" onClick={() => goTo("input")}>
            원문 보기
          </button>
        </div>
        <div className="redline-copy">{renderRedline(state.input.original_text, analyze.flagged_spans)}</div>
        <div className="risk-legend">
          {categoryList.map((category, index) => (
            <span key={category}>
              <b>{index + 1}</b>
              {riskCategoryKo(category)}
            </span>
          ))}
        </div>
        <small className="character-count">문자 수 {state.input.original_text.length} / 2,000</small>
      </section>

      <aside className="inspector">
        <div className={`risk-score risk-${analyze.risk_level.toLowerCase()}`}>
          <span>위험도</span>
          <strong>{analyze.risk_level}</strong>
        </div>
        <div className="confidence-row">
          <span>신뢰도</span>
          <strong>{confidence}%</strong>
        </div>
        <h2>탐지 리스크</h2>
        <p>{analyze.reviewer_notes}</p>
        <div className="risk-metrics">
          <span>
            <strong>{analyze.flagged_spans.length}</strong>
            탐지 표현
          </span>
          <span>
            <strong>{analyze.risk_categories.length}</strong>
            리스크 유형
          </span>
        </div>
      </aside>

      <section className="risk-carousel-section" aria-label="탐지 리스크 상세">
        <button
          className="carousel-button"
          onClick={() => setRiskPage((page) => Math.max(0, page - 1))}
          disabled={safePage === 0}
          aria-label="이전 리스크"
        >
          &lt;
        </button>
        <div className="risk-carousel-window">
          {activeSpan ? (
            <article key={`${activeSpan.span_text}-${activeSpan.start}`} className="span-card risk-slide">
              <div className="risk-slide-index">{safePage + 1}</div>
              <strong>{activeSpan.span_text}</strong>
              <span>
                {riskCategoryKo(activeSpan.risk_category)} · {sourceLabel(activeSpan.source)}
              </span>
              <small>{riskReasonKo(activeSpan)}</small>
              <em>신뢰도 {Math.round(activeSpan.confidence * 100)}%</em>
            </article>
          ) : (
            <article className="span-card risk-slide">
              <strong>탐지된 리스크가 없습니다.</strong>
              <small>현재 문구는 자동 탐지 기준상 추가 확인 항목이 없습니다.</small>
            </article>
          )}
        </div>
        <button
          className="carousel-button"
          onClick={() => setRiskPage((page) => Math.min(flaggedSpans.length - 1, page + 1))}
          disabled={!flaggedSpans.length || safePage >= flaggedSpans.length - 1}
          aria-label="다음 리스크"
        >
          &gt;
        </button>
        <span className="carousel-count">
          {flaggedSpans.length ? safePage + 1 : 0} / {flaggedSpans.length}
        </span>
      </section>

      <div className="action-row">
        <button className="secondary-button" onClick={() => goTo("input")}>
          문구 수정
        </button>
        <button className="primary-button" onClick={loadEvidence} disabled={state.isLoading}>
          근거 확인
        </button>
      </div>
    </div>
  );
}

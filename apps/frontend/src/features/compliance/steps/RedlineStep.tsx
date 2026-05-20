import { renderRedline } from "../../../components/redline/renderRedline";
import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function RedlineStep({ workflow }: StepProps) {
  const { state, loadEvidence, goTo } = workflow;
  const analyze = state.analyze;

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
          {analyze.risk_categories.map((category) => (
            <span key={category}>{category}</span>
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
        <div className="span-list">
          {analyze.flagged_spans.map((span) => (
            <article key={`${span.span_text}-${span.start}`} className="span-card">
              <strong>{span.span_text}</strong>
              <span>{span.risk_category}</span>
              <small>{span.reason}</small>
              <em>신뢰도 {Math.round(span.confidence * 100)}%</em>
            </article>
          ))}
        </div>
      </aside>

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

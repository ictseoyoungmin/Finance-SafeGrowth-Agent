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

  return (
    <div className="review-layout">
      <div className="redline-copy">{renderRedline(state.input.original_text, analyze.flagged_spans)}</div>

      <aside className="inspector">
        <div className={`risk-score risk-${analyze.risk_level.toLowerCase()}`}>
          <span>Risk</span>
          <strong>{analyze.risk_level}</strong>
        </div>
        <p>{analyze.reviewer_notes}</p>
        <div className="span-list">
          {analyze.flagged_spans.map((span) => (
            <article key={`${span.span_text}-${span.start}`} className="span-card">
              <strong>{span.span_text}</strong>
              <span>{span.risk_category}</span>
              <small>{span.reason}</small>
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

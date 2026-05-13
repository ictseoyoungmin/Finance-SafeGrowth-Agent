import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function ApprovalStep({ workflow }: StepProps) {
  const { state, goTo, reset } = workflow;
  const analyze = state.analyze;
  const rewrite = state.rewrite;

  return (
    <div className="approval-layout">
      <section className="approval-summary">
        <p className="eyebrow">Decision</p>
        <h2>CONDITIONALLY_APPROVED</h2>
        <p>주요 수정 사항 반영 후 배포 가능</p>
      </section>

      <section className="package-grid">
        <article>
          <span>Content ID</span>
          <strong>{analyze?.content_id ?? "demo-content"}</strong>
        </article>
        <article>
          <span>Risk Level</span>
          <strong>{analyze?.risk_level ?? "HIGH"}</strong>
        </article>
        <article>
          <span>Flagged Spans</span>
          <strong>{analyze?.flagged_spans.length ?? 0}</strong>
        </article>
        <article>
          <span>Reviewer</span>
          <strong>김준법 수석</strong>
        </article>
      </section>

      <section className="final-copy">
        <h2>배포 후보 문구</h2>
        <p>{rewrite?.revised_text_marketing}</p>
      </section>

      <div className="action-row">
        <button className="secondary-button" onClick={() => goTo("rewrite")}>
          수정안으로
        </button>
        <button className="secondary-button" onClick={reset}>
          새 검토
        </button>
      </div>
    </div>
  );
}

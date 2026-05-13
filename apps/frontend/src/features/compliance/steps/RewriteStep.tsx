import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function RewriteStep({ workflow }: StepProps) {
  const { state, goTo } = workflow;
  const rewrite = state.rewrite;

  if (!rewrite) {
    return null;
  }

  return (
    <div className="rewrite-layout">
      <article className="comparison-panel">
        <h2>보수적 수정안</h2>
        <p>{rewrite.revised_text_conservative}</p>
      </article>
      <article className="comparison-panel">
        <h2>마케팅 유지 수정안</h2>
        <p>{rewrite.revised_text_marketing}</p>
      </article>

      <div className="changes-table">
        {rewrite.changes.map((change) => (
          <article key={`${change.original}-${change.replacement}`} className="change-row">
            <strong>{change.original}</strong>
            <span>{change.replacement}</span>
            <p>{change.reason}</p>
          </article>
        ))}
      </div>

      <div className="action-row">
        <button className="secondary-button" onClick={() => goTo("redline")}>
          위험 다시 보기
        </button>
        <button className="primary-button" onClick={() => goTo("approval")}>
          승인 패키지
        </button>
      </div>
    </div>
  );
}

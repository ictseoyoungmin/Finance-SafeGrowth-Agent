import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function EvidenceStep({ workflow }: StepProps) {
  const { state, loadRewrite, goTo } = workflow;
  const evidence = state.evidence;

  if (!evidence) {
    return null;
  }

  return (
    <div className="evidence-layout">
      <div className="evidence-list">
        {evidence.evidence_list.map((item) => (
          <article key={item.evidence_id} className="evidence-card">
            <div>
              <strong>{item.title}</strong>
              <span>{item.version}</span>
            </div>
            <p>{item.snippet}</p>
            <small>similarity {Math.round(item.similarity * 100)}%</small>
          </article>
        ))}
      </div>

      <aside className="guideline-panel">
        <h2>Guidelines</h2>
        {evidence.guideline_snippets.map((snippet) => (
          <p key={snippet}>{snippet}</p>
        ))}
      </aside>

      <div className="action-row">
        <button className="secondary-button" onClick={() => goTo("redline")}>
          Redline으로
        </button>
        <button className="primary-button" onClick={loadRewrite} disabled={state.isLoading}>
          수정안 생성
        </button>
      </div>
    </div>
  );
}

import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function RewriteStep({ workflow }: StepProps) {
  const { state, goTo, selectRevision } = workflow;
  const rewrite = state.rewrite;

  if (!rewrite) {
    return null;
  }

  const selectedFinalText =
    state.selectedRevision === "conservative"
      ? rewrite.revised_text_conservative
      : rewrite.revised_text_marketing;

  return (
    <div className="rewrite-screen">
      <header className="panel-heading">
        <h2>수정안 비교</h2>
        <p>AI가 마케팅 의도를 유지하면서 컴플라이언스에 적합한 표현으로 대체 제안했습니다.</p>
      </header>

      <div className="mode-strip">비교 모드: 마케팅 의도 유지 모드</div>

      <div className="rewrite-table">
        <div className="rewrite-header">항목</div>
        <div className="rewrite-header">원문 (위험 표현)</div>
        <div className="rewrite-header arrow-cell" />
        <div className="rewrite-header">수정안 (AI 제안)</div>
        {rewrite.changes.map((change, index) => (
          <article key={`${change.original}-${change.replacement}`} className="rewrite-row">
            <strong>{index + 1}</strong>
            <div>
              <mark className="delete-mark">{change.original}</mark>
              <small>위험 사유</small>
              <p>{change.reason}</p>
            </div>
            <span className="arrow-cell">→</span>
            <div>
              <mark className="add-mark">{change.replacement}</mark>
              <small>개선 포인트</small>
              <p>오인 가능성을 낮추고 필수 고지 맥락을 보강합니다.</p>
            </div>
          </article>
        ))}
      </div>

      <div className="revision-actions">
        <button
          className={`choice-button ${state.selectedRevision === "conservative" ? "is-selected" : ""}`}
          onClick={() => selectRevision("conservative")}
        >
          보수적 수정안 적용
          <small>리스크 최소화 중심</small>
        </button>
        <button
          className={`choice-button ${state.selectedRevision === "marketing" ? "is-selected" : ""}`}
          onClick={() => selectRevision("marketing")}
        >
          마케팅 유지 수정안 적용
          <small>마케팅 의도 최대한 유지</small>
        </button>
        <button className="choice-button" onClick={() => goTo("input")}>
          직접 수정
          <small>직접 편집하여 반영</small>
        </button>
      </div>

      <section className="selected-revision-panel">
        <div>
          <span>최종 선택 문안</span>
          <strong>
            {state.selectedRevision === "conservative" ? "보수적 수정안" : "마케팅 유지 수정안"}
          </strong>
        </div>
        <p>{selectedFinalText}</p>
      </section>

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

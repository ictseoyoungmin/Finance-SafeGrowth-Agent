import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function ApprovalStep({ workflow }: StepProps) {
  const { state, goTo, loadReport, reset, submitApproval } = workflow;
  const analyze = state.analyze;
  const rewrite = state.rewrite;
  const finalText =
    state.selectedRevision === "conservative"
      ? rewrite?.revised_text_conservative
      : rewrite?.revised_text_marketing;

  return (
    <div className="approval-layout">
      <section className="approval-hero">
        <div>
          <h2>최종 승인 요약</h2>
          <p>준법감시팀의 심의 결과와 최종 문안을 확인하고 승인 절차를 진행해주세요.</p>
        </div>
        <div className="reviewer-card">
          <span className="avatar">A</span>
          <strong>김준법 수석</strong>
          <small>Compliance Manager</small>
        </div>
      </section>

      <section className="decision-banner">
        <span>심의</span>
        <div>
          <h2>심의 결과: {state.approval?.decision ?? "조건부 승인 권고"}</h2>
          <p>{state.actionMessage ?? "아래 주요 수정 사항을 반영하여 최종 승인하시기를 권고드립니다."}</p>
        </div>
      </section>

      <section className="package-grid">
        <article>
          <h2>주요 수정 사항</h2>
          {rewrite?.changes.map((change, index) => (
            <p key={change.original}>
              <strong>{index + 1}</strong> {change.replacement}
            </p>
          ))}
        </article>
        <article>
          <h2>남은 검토 필요</h2>
          <p>실제 상품 수익률 산정 기준 확인 필요</p>
          <p>이벤트 조건 및 기간 확인 필요</p>
        </article>
        <article>
          <h2>관련 근거</h2>
          <p>금융소비자보호 가이드라인</p>
          <p>금융투자상품 광고 심사지침</p>
          <p>검토 ID: {analyze?.content_id ?? "demo-content"}</p>
          {state.report ? <p>리포트: {state.report.summary}</p> : null}
        </article>
      </section>

      <section className="final-copy">
        <div className="panel-heading compact">
          <h2>최종 문안</h2>
          <small>{finalText?.length ?? 0} / 2,000</small>
        </div>
        <p>{finalText}</p>
      </section>

      <div className="action-row">
        <button
          className="primary-button"
          disabled={state.isLoading}
          onClick={() => submitApproval("CONDITIONALLY_APPROVED")}
        >
          승인
        </button>
        <button className="danger-button" disabled={state.isLoading} onClick={() => submitApproval("REJECTED")}>
          반려
        </button>
        <button
          className="warning-button"
          disabled={state.isLoading}
          onClick={() => submitApproval("REVISION_REQUESTED")}
        >
          수정 요청
        </button>
        <button className="secondary-button" disabled={state.isLoading} onClick={loadReport}>
          리포트 확인
        </button>
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

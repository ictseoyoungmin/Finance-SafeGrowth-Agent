import { useEffect, useRef } from "react";

import { useAuth } from "../../auth/AuthContext";
import { ApprovalStamp } from "../components/ApprovalStamp";
import { ReportPackagePanel } from "../components/ReportPackagePanel";
import { approvalDecisionLabel } from "../approvalDecisionLabels";
import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function ApprovalStep({ workflow }: StepProps) {
  const { state, goTo, loadReport, reset, submitApproval } = workflow;
  const { profile } = useAuth();
  const reviewerName = profile?.display_name ?? "Compliance Reviewer";
  const reviewerTitle = profile?.title ?? "Compliance Manager";
  const avatarInitial = reviewerName[0] ?? "C";
  const decisionBannerRef = useRef<HTMLElement>(null);
  const analyze = state.analyze;
  const rewrite = state.rewrite;
  const finalText =
    state.selectedRevision === "conservative"
      ? rewrite?.revised_text_conservative
      : rewrite?.revised_text_marketing;
  const evidenceCount = state.evidence?.evidence_list.length ?? 0;
  const decisionLabel = approvalDecisionLabel(state.approval?.decision);
  const isSavingDecision =
    state.pendingAction === "approve" ||
    state.pendingAction === "reject" ||
    state.pendingAction === "request_revision";
  const isApprovalSaved = Boolean(state.approval);

  useEffect(() => {
    if (!state.approval || !decisionBannerRef.current) return;
    const rect = decisionBannerRef.current.getBoundingClientRect();
    const isOutsideViewport = rect.top < 0 || rect.bottom > window.innerHeight;
    if (isOutsideViewport) {
      decisionBannerRef.current.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [state.approval]);

  return (
    <div className="approval-layout">
      <section className="approval-hero">
        <div>
          <h2>최종 승인 요약</h2>
          <p>준법감시팀의 심의 결과와 최종 문안을 확인하고 승인 절차를 진행해주세요.</p>
        </div>
        <div className="reviewer-card">
          <span className="avatar">{avatarInitial}</span>
          <strong>{reviewerName}</strong>
          <small>{reviewerTitle}</small>
        </div>
        <ApprovalStamp decision={state.approval?.decision} />
      </section>

      <section
        ref={decisionBannerRef}
        className={`decision-banner ${isApprovalSaved ? "is-saved" : ""} ${isSavingDecision ? "is-saving" : ""}`}
        role={isApprovalSaved ? "status" : undefined}
      >
        <span>{isApprovalSaved ? "완료" : isSavingDecision ? "저장" : "심의"}</span>
        <div>
          <h2>
            {isSavingDecision
              ? `${state.actionMessage ?? "심의 결과 저장 중..."}`
              : `심의 결과: ${decisionLabel}`}
          </h2>
          <p>
            {isApprovalSaved
              ? `방금 ${reviewerName} 이름으로 ${decisionLabel} 결과가 저장되었습니다.`
              : state.actionMessage ?? "아래 주요 수정 사항을 반영하여 최종 승인하시기를 권고드립니다."}
          </p>
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
          <p>근거 문서 {evidenceCount}건 연결</p>
          {state.evidence?.evidence_list.slice(0, 2).map((item) => (
            <p key={item.evidence_id}>{item.title}</p>
          ))}
          <p>검토 ID: {analyze?.content_id ?? "demo-content"}</p>
        </article>
      </section>

      <section className="final-copy">
        <div className="panel-heading compact">
          <h2>최종 문안</h2>
          <small>{finalText?.length ?? 0} / 2,000</small>
        </div>
        <p>{finalText}</p>
      </section>

      {state.report ? (
        <ReportPackagePanel
          report={state.report}
          helperText="이 리포트는 DB에 저장되었습니다. 좌측 '검토 이력'에서 다시 조회할 수 있습니다."
        />
      ) : null}

      {state.errorMessage ? (
        <div
          className="action-feedback is-error"
          role="alert"
        >
          <strong>저장 실패</strong>
          <span>{state.errorMessage}</span>
        </div>
      ) : null}

      <div className="approval-actions">
        <button
          className="primary-button"
          disabled={state.isLoading}
          aria-busy={state.pendingAction === "approve"}
          onClick={() => submitApproval("CONDITIONALLY_APPROVED")}
        >
          {state.pendingAction === "approve" ? "조건부 승인 저장 중..." : "조건부 승인"}
        </button>
        <button
          className="danger-button"
          disabled={state.isLoading}
          aria-busy={state.pendingAction === "reject"}
          onClick={() => submitApproval("REJECTED")}
        >
          {state.pendingAction === "reject" ? "반려 저장 중..." : "반려"}
        </button>
        <button
          className="warning-button"
          disabled={state.isLoading}
          aria-busy={state.pendingAction === "request_revision"}
          onClick={() => submitApproval("REVISION_REQUESTED")}
        >
          {state.pendingAction === "request_revision" ? "수정 요청 저장 중..." : "수정 요청"}
        </button>
        <button
          className="secondary-button"
          disabled={state.isLoading}
          aria-busy={state.pendingAction === "load_report"}
          onClick={loadReport}
        >
          {state.pendingAction === "load_report"
            ? "리포트 불러오는 중..."
            : state.report
              ? "리포트 패키지 다시 보기"
              : "리포트 패키지 보기"}
        </button>
        <button className="secondary-button" onClick={() => goTo("rewrite")}>
          수정안으로
        </button>
        <button className="secondary-button" onClick={reset}>
          처음으로
        </button>
      </div>
    </div>
  );
}

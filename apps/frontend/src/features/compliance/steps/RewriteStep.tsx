import { useMemo } from "react";

import { HelpHint } from "../../../components/HelpHint";
import type { ComplianceWorkflow } from "../store";
import type {
  FlaggedSpan,
  RevisionValidation,
  RewriteAttempt,
  RiskLevel,
} from "../types";

interface StepProps {
  workflow: ComplianceWorkflow;
}

const FALLBACK_HINT =
  "Gemini API 호출이 실패했거나 응답 형식이 예상과 달라, 입력 문장 기반 결정형 규칙(rule-based)으로 수정안을 생성했습니다. 결과는 안전한 표현 완화 중심이며, 실제 LLM 결과 대비 다양성이 낮을 수 있습니다.";

const STATUS_LABEL: Record<string, string> = {
  ok: "성공",
  rate_limited: "사용량 초과",
  auth_error: "인증 실패",
  transient: "일시 오류",
  parse_error: "형식 오류",
  empty: "응답 없음",
};

function summarizeAttempts(attempts: RewriteAttempt[]): string {
  if (attempts.length === 0) return "";
  return attempts
    .map((attempt, index) => {
      const label = STATUS_LABEL[attempt.status] ?? attempt.status;
      return `${index + 1}/${attempts.length} ${attempt.model} · ${label}`;
    })
    .join("  →  ");
}

function renderValidationChip(label: string, v?: RevisionValidation | null) {
  if (!v) return null;
  const level = v.risk_level;
  const tone =
    level === "HIGH" ? "is-high" : level === "MEDIUM" ? "is-medium" : "is-low";
  const counts = `HIGH ${v.residual_high} · MEDIUM ${v.residual_medium} · LOW ${v.residual_low}`;
  return (
    <div className={`revision-validation ${tone}`}>
      <strong>
        {label} · 잔존 위험 {level}
      </strong>
      <small>{counts}</small>
      {v.residual_high > 0 ? (
        <em>※ HIGH 잔존 — 추가 검토 권장</em>
      ) : null}
    </div>
  );
}

function lookupSeverity(
  original: string,
  spans: FlaggedSpan[],
): RiskLevel | undefined {
  const trimmed = original.trim();
  if (!trimmed) return undefined;
  // exact match first
  const exact = spans.find((span) => span.span_text === trimmed);
  if (exact) return exact.severity;
  // original contains span_text
  const contains = spans.find(
    (span) => span.span_text && trimmed.includes(span.span_text),
  );
  if (contains) return contains.severity;
  // span_text contains original
  const contained = spans.find(
    (span) => span.span_text && span.span_text.includes(trimmed),
  );
  return contained?.severity;
}

export function RewriteStep({ workflow }: StepProps) {
  const { state, goTo, selectRevision } = workflow;
  const rewrite = state.rewrite;
  const analyzeSpans = useMemo(
    () => state.analyze?.flagged_spans ?? [],
    [state.analyze?.flagged_spans],
  );

  if (!rewrite) {
    return null;
  }
  const selectedFinalText =
    state.selectedRevision === "conservative"
      ? rewrite.revised_text_conservative
      : rewrite.revised_text_marketing;
  const isLlmSource = rewrite.source === "gemini" || rewrite.source === "llm";
  const sourceLabel = isLlmSource
    ? `Gemini 검수 결과${rewrite.model_version ? ` · ${rewrite.model_version}` : ""}`
    : "기본 패턴 기반 (fallback)";
  const attempts = rewrite.attempts ?? [];
  const attemptSummary = summarizeAttempts(attempts);
  const successAttemptIndex = attempts.findIndex((a) => a.status === "ok");
  const showAttemptSummary = attempts.length > 1 || (attempts.length === 1 && attempts[0].status !== "ok");

  return (
    <div className="rewrite-screen">
      <header className="panel-heading">
        <h2>수정안 비교</h2>
        <p>AI가 마케팅 의도를 유지하면서 컴플라이언스에 적합한 표현으로 대체 제안했습니다.</p>
      </header>

      <div className="rewrite-status-row">
        <div className="mode-strip">비교 모드: 마케팅 의도 유지 모드</div>
        <span className={`rewrite-source ${isLlmSource ? "is-gemini" : "is-fallback"}`}>
          {sourceLabel}
          {isLlmSource ? null : <HelpHint hint={FALLBACK_HINT} align="right" />}
        </span>
      </div>

      {showAttemptSummary ? (
        <div
          className={`rewrite-attempts ${
            isLlmSource && successAttemptIndex >= 0 ? "is-recovered" : "is-failed"
          }`}
          role="status"
        >
          <strong>
            {isLlmSource && successAttemptIndex >= 0
              ? `Gemini 호출 ${successAttemptIndex + 1}/${attempts.length} 회만에 성공`
              : `Gemini 호출 ${attempts.length}/${attempts.length} 모두 실패 → 기본 패턴으로 응답`}
          </strong>
          <small>{attemptSummary}</small>
        </div>
      ) : null}

      <div className="rewrite-table">
        <div className="rewrite-header">항목</div>
        <div className="rewrite-header">원문 (위험 표현)</div>
        <div className="rewrite-header arrow-cell" />
        <div className="rewrite-header">수정안 (AI 제안)</div>
        {rewrite.changes.length > 0 ? rewrite.changes.map((change, index) => {
          const unchanged = change.original.trim() === change.replacement.trim();
          const severity = lookupSeverity(change.original, analyzeSpans);
          const severityClass = severity ? ` severity-${severity}` : "";
          const unchangedClass = unchanged ? " is-unchanged" : "";
          return (
          <article key={`${change.original}-${change.replacement}-${index}`} className={`rewrite-row${unchangedClass}`}>
            <strong>{index + 1}</strong>
            <div>
              <mark className={`delete-mark${severityClass}${unchangedClass}`}>{change.original}</mark>
              <small className={unchanged ? "is-unchanged" : ""}>
                {unchanged ? "유지" : "위험 사유"}
              </small>
              <p>{unchanged ? "원문이 그대로 유지됩니다. 별도 위험 표현은 식별되지 않았습니다." : change.reason}</p>
            </div>
            <span className="arrow-cell">→</span>
            <div>
              <mark className={`add-mark${unchangedClass}`}>{change.replacement}</mark>
              <small className={unchanged ? "is-unchanged" : ""}>
                {unchanged ? "변경 없음" : "개선 포인트"}
              </small>
              <p>{unchanged ? "수정안에서도 동일한 표현이 사용됩니다." : "오인 가능성을 낮추고 필수 고지 맥락을 보강합니다."}</p>
            </div>
          </article>
          );
        }) : (
          <article className="rewrite-row">
            <strong>1</strong>
            <div>
              <mark className="delete-mark">전체 문안</mark>
              <small>위험 사유</small>
              <p>변경 항목이 비어 있어 최종 수정 문안을 기준으로 검토합니다.</p>
            </div>
            <span className="arrow-cell">→</span>
            <div>
              <mark className="add-mark">최종 선택 문안</mark>
              <small>개선 포인트</small>
              <p>원문 대비 필수 고지와 오인 방지 표현을 확인합니다.</p>
            </div>
          </article>
        )}
      </div>

      {(rewrite.validation_conservative || rewrite.validation_marketing) ? (
        <div className="revision-validations">
          {renderValidationChip("보수적 수정안", rewrite.validation_conservative)}
          {renderValidationChip("마케팅 유지 수정안", rewrite.validation_marketing)}
        </div>
      ) : null}

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

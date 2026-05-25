import { useMemo, useState } from "react";

import { EvidenceSourceModal } from "../components/EvidenceSourceModal";
import { riskCategoryKo, riskReasonKo, sourceLabel } from "../riskPresentation";
import type { ComplianceWorkflow } from "../store";
import type { EvidenceItem, FlaggedSpan } from "../types";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function EvidenceStep({ workflow }: StepProps) {
  const { state, loadRewrite, goTo } = workflow;
  const evidence = state.evidence;
  const risks = useMemo(() => state.analyze?.flagged_spans ?? [], [state.analyze?.flagged_spans]);
  const [selectedRiskIndex, setSelectedRiskIndex] = useState(0);
  const [openVersionId, setOpenVersionId] = useState<string | undefined>();
  const [openTitle, setOpenTitle] = useState<string | undefined>();

  if (!evidence) {
    return null;
  }

  const selectedRisk = risks[selectedRiskIndex];
  const allEvidence = evidence.evidence_list;
  const matched = matchEvidenceForRisk(allEvidence, selectedRisk);
  const otherEvidence = allEvidence.filter((item) => !matched.includes(item));

  return (
    <div className="evidence-layout-v2">
      <header className="panel-heading evidence-head">
        <div>
          <h2>근거 패널</h2>
          <p>좌측에서 리스크를 선택하면 매칭된 규정 근거와 DB 인스턴스를 확인할 수 있습니다.</p>
        </div>
        <div className="evidence-head__metrics">
          <span>
            <strong>{risks.length}</strong>
            탐지 표현
          </span>
          <span>
            <strong>{allEvidence.length}</strong>
            참조 근거
          </span>
          <span>
            <strong>{state.analyze?.risk_level ?? "—"}</strong>
            위험도
          </span>
        </div>
      </header>

      <div className="evidence-grid">
        <aside className="evidence-risk-list" aria-label="탐지 리스크 목록">
          <p className="evidence-section-title">탐지 리스크</p>
          {risks.length === 0 ? (
            <p className="evidence-empty">탐지된 리스크가 없습니다.</p>
          ) : (
            <ul>
              {risks.map((risk, index) => {
                const isActive = index === selectedRiskIndex;
                return (
                  <li key={`${risk.span_text}-${risk.start}`}>
                    <button
                      type="button"
                      className={`evidence-risk-button ${isActive ? "is-active" : ""}`}
                      onClick={() => setSelectedRiskIndex(index)}
                      aria-pressed={isActive}
                    >
                      <span className="evidence-risk-number">{index + 1}</span>
                      <span className="evidence-risk-text">
                        <strong>{risk.span_text}</strong>
                        <small>{riskCategoryKo(risk.risk_category)}</small>
                      </span>
                      <span className={`badge ${severityBadgeClass(risk.severity)}`}>
                        {risk.severity}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </aside>

        <section className="evidence-match" aria-label="매칭된 근거">
          {selectedRisk ? (
            <div className="evidence-match-head">
              <p className="evidence-section-title">선택 리스크</p>
              <div className="evidence-match-headline">
                <strong>
                  <span className="evidence-risk-number">{selectedRiskIndex + 1}</span>
                  {selectedRisk.span_text}
                </strong>
                <small>{riskCategoryKo(selectedRisk.risk_category)} · {sourceLabel(selectedRisk.source)}</small>
              </div>
              <p className="evidence-match-reason">{riskReasonKo(selectedRisk)}</p>
            </div>
          ) : null}

          {matched.length > 0 ? (
            <div className="evidence-cards">
              <p className="evidence-section-title">매칭된 근거 ({matched.length})</p>
              {matched.map((item) => (
                <EvidenceCard
                  key={item.evidence_id}
                  item={item}
                  emphasized
                  onOpenSource={() => {
                    if (item.version_id) {
                      setOpenVersionId(item.version_id);
                      setOpenTitle(item.title);
                    }
                  }}
                />
              ))}
            </div>
          ) : (
            <p className="evidence-empty">선택한 리스크 카테고리에 직접 매칭된 근거가 없습니다.</p>
          )}

          {otherEvidence.length > 0 ? (
            <div className="evidence-cards">
              <p className="evidence-section-title evidence-section-title--muted">
                같은 검토에 포함된 다른 근거
              </p>
              {otherEvidence.map((item) => (
                <EvidenceCard
                  key={item.evidence_id}
                  item={item}
                  onOpenSource={() => {
                    if (item.version_id) {
                      setOpenVersionId(item.version_id);
                      setOpenTitle(item.title);
                    }
                  }}
                />
              ))}
            </div>
          ) : null}
        </section>
      </div>

      <div className="info-strip">
        위 근거는 내부 규정·가이드라인 DB를 기반으로 제공되며, 필요 시 관련 법령을 추가로 확인하시기 바랍니다.
      </div>

      <div className="action-row">
        <button className="secondary-button" onClick={() => goTo("redline")}>
          Redline으로
        </button>
        <button
          className="primary-button"
          onClick={loadRewrite}
          disabled={state.isLoading}
          aria-busy={state.isLoading}
        >
          {state.isLoading ? "수정안 생성 중..." : "수정안 생성"}
        </button>
      </div>

      {openVersionId ? (
        <EvidenceSourceModal
          versionId={openVersionId}
          evidenceTitle={openTitle}
          onClose={() => {
            setOpenVersionId(undefined);
            setOpenTitle(undefined);
          }}
        />
      ) : null}
    </div>
  );
}

interface EvidenceCardProps {
  item: EvidenceItem;
  emphasized?: boolean;
  onOpenSource: () => void;
}

function EvidenceCard({ item, emphasized = false, onOpenSource }: EvidenceCardProps) {
  return (
    <article className={`evidence-card-v2 ${emphasized ? "is-emphasized" : ""}`}>
      <header className="evidence-card-v2__head">
        <strong>{item.title}</strong>
        <span className="evidence-card-v2__similarity">관련도 {Math.round(item.similarity * 100)}%</span>
      </header>
      <p className="evidence-card-v2__snippet">{item.snippet}</p>
      <footer className="evidence-card-v2__foot">
        <small>
          {item.version}
          {item.effective_date ? ` · 시행일 ${item.effective_date}` : ""}
        </small>
        <button
          type="button"
          className="ghost-button"
          onClick={onOpenSource}
          disabled={!item.version_id}
          title={item.version_id ? undefined : "데모 데이터 — DB 인스턴스 없음"}
        >
          DB 인스턴스 보기
        </button>
      </footer>
      {item.risk_categories && item.risk_categories.length > 0 ? (
        <div className="evidence-card-v2__tags">
          {item.risk_categories.map((cat) => (
            <span key={cat} className="badge badge--neutral">
              {riskCategoryKo(cat)}
            </span>
          ))}
        </div>
      ) : null}
    </article>
  );
}

function matchEvidenceForRisk(items: EvidenceItem[], risk: FlaggedSpan | undefined): EvidenceItem[] {
  if (!risk) return items;
  const matched = items.filter((item) =>
    (item.risk_categories ?? []).some((cat) => cat === risk.risk_category),
  );
  if (matched.length > 0) return matched;
  // fallback: positional matching by index (first risk → first evidence)
  return items.length > 0 ? [items[0]] : [];
}

function severityBadgeClass(severity: FlaggedSpan["severity"]): string {
  if (severity === "HIGH") return "badge--high";
  if (severity === "MEDIUM") return "badge--med";
  return "badge--low";
}

import { riskCategoryKo, riskReasonKo, sourceLabel } from "../riskPresentation";
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

  const risks = state.analyze?.flagged_spans ?? [];
  const firstRisk = risks[0];

  return (
    <div className="evidence-layout">
      <section className="risk-context-panel">
        <div className="panel-heading compact">
          <div>
            <h2>리스크 검토 대상 문장</h2>
            <p>AI가 잠재적 오인 소지가 있는 문장을 탐지했습니다.</p>
          </div>
          <small className="character-count">{state.input.original_text.length} / 2,000</small>
        </div>
        <div className="risk-context-copy">
          <strong>{firstRisk?.severity === "HIGH" ? "고위험" : "검토 필요"}</strong>
          <p>{state.input.original_text}</p>
        </div>
        <div className="sentence-evidence-map">
          {risks.map((risk, index) => (
            <article key={`${risk.span_text}-${risk.start}`} className="sentence-map-card">
              <span className="risk-number">{index + 1}</span>
              <div>
                <strong>{risk.span_text}</strong>
                <small>
                  참조 근거 {(index % Math.max(evidence.evidence_list.length, 1)) + 1} · {sourceLabel(risk.source)}
                </small>
              </div>
            </article>
          ))}
        </div>
      </section>

      <aside className="guideline-panel summary">
        <div className="panel-heading compact">
          <h2>검토 요약</h2>
          <span>관련 규정 {evidence.evidence_list.length}건</span>
        </div>
        <div className="summary-score-row">
          <span>
            <strong>{risks.length}</strong>
            탐지 표현
          </span>
          <span>
            <strong>{evidence.evidence_list.length}</strong>
            참조 근거
          </span>
        </div>
        <dl>
          <div>
            <dt>탐지 사유</dt>
            <dd>{state.analyze?.risk_categories.map(riskCategoryKo).join(", ")}</dd>
          </div>
          <div>
            <dt>리스크 수준</dt>
            <dd>{state.analyze?.risk_level}</dd>
          </div>
          <div>
            <dt>검토 기준</dt>
            <dd>금융상품 광고 준수 규정</dd>
          </div>
          <div>
            <dt>선택 문맥</dt>
            <dd>{firstRisk ? `${firstRisk.span_text} · ${riskReasonKo(firstRisk)}` : "표준 데모 문구"}</dd>
          </div>
        </dl>
      </aside>

      <section className="evidence-section">
        <div className="panel-heading compact">
          <div>
            <h2>근거 패널</h2>
            <p>해당 리스크 판단은 아래의 규정 및 가이드라인을 근거로 합니다.</p>
          </div>
        </div>
        <div className="evidence-link-strip">
          {risks.map((risk, index) => (
            <span key={`${risk.span_text}-link-${index}`}>
              리스크 {index + 1} ↔ 근거 {(index % Math.max(evidence.evidence_list.length, 1)) + 1}
            </span>
          ))}
        </div>
        <div className="evidence-list">
          {evidence.evidence_list.map((item, index) => (
            <article key={item.evidence_id} className="evidence-card">
              <strong>
                <span className="evidence-number">{index + 1}</span>
                참조 근거
              </strong>
              <div>
                <p>{item.snippet}</p>
                <button className="ghost-button">원문 보기</button>
              </div>
              <small>
                {item.title} · {item.version} · 관련도 {Math.round(item.similarity * 100)}%
              </small>
              {evidence.guideline_snippets[index] ? (
                <em>{evidence.guideline_snippets[index]}</em>
              ) : null}
              <div className="matched-risk-row">
                {risks
                  .filter((_, riskIndex) => riskIndex % Math.max(evidence.evidence_list.length, 1) === index)
                  .map((risk, riskIndex) => (
                    <span key={`${risk.span_text}-${riskIndex}`}>리스크 {risks.indexOf(risk) + 1}</span>
                  ))}
              </div>
            </article>
          ))}
        </div>
        <div className="info-strip">
          위 근거는 내부 규정·가이드라인 DB를 기반으로 제공되며, 필요 시 관련 법령을 추가로
          확인하시기 바랍니다.
        </div>
      </section>

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

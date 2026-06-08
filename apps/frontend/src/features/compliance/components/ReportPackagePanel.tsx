import { approvalDecisionLabel } from "../approvalDecisionLabels";
import type { ApprovalDecision, ReportResponse } from "../types";

interface ReportPackagePanelProps {
  report: ReportResponse;
  helperText?: string;
}

export function ReportPackagePanel({ report, helperText }: ReportPackagePanelProps) {
  const decision = report.approval?.decision as ApprovalDecision | undefined;
  const reviewer = (report.approval?.reviewer as string | undefined) ?? "기록 없음";
  const createdAt = report.approval?.created_at as string | undefined;
  const finalText = report.final_text || "최종 문안 정보가 없습니다.";

  return (
    <section className="report-package" aria-label="리포트 패키지">
      <header className="panel-heading compact report-package__head">
        <div>
          <h2>리포트 패키지</h2>
          <p>이 검토건의 저장된 결과입니다.</p>
        </div>
        <span className="run-pill trace-done">저장 완료</span>
      </header>

      <dl className="report-package__grid">
        <div>
          <dt>검토 ID</dt>
          <dd className="is-mono">{report.content_id}</dd>
        </div>
        <div>
          <dt>심의 결정</dt>
          <dd>
            {decision ? approvalDecisionLabel(decision) : "미승인"}
            {decision ? <small className="report-package__sub">{decision}</small> : null}
          </dd>
        </div>
        <div>
          <dt>리스크 레벨</dt>
          <dd>{report.risk_level ?? "정보 없음"}</dd>
        </div>
        <div>
          <dt>검토자</dt>
          <dd>{reviewer}</dd>
        </div>
        <div>
          <dt>감사 로그</dt>
          <dd>{report.audit_log.length}건</dd>
        </div>
        {createdAt ? (
          <div>
            <dt>승인 시각</dt>
            <dd>{formatTimestamp(createdAt)}</dd>
          </div>
        ) : null}
      </dl>

      <div className="report-package__final">
        <p className="report-package__final-label">최종 문안</p>
        <p className="report-package__final-text">{finalText}</p>
      </div>

      <ReportChangesSection changes={report.changes} />
      <ReportEvidenceSection evidence={report.evidence} />

      {helperText ? <p className="report-package__hint">{helperText}</p> : null}
    </section>
  );
}

function ReportChangesSection({ changes }: { changes: ReportResponse["changes"] }) {
  if (!changes || changes.length === 0) return null;
  return (
    <div className="report-package__section">
      <p className="report-package__section-label">수정 전후 ({changes.length}건)</p>
      <ul className="report-package__changes">
        {changes.map((change, index) => {
          const original = String(change.original ?? "");
          const replacement = String(change.replacement ?? "");
          const reason = change.reason ? String(change.reason) : "";
          const category = change.risk_category ? String(change.risk_category) : "";
          return (
            <li key={`${original}-${index}`} className="report-package__change">
              <div className="report-package__change-row">
                <span className="report-package__change-orig">{original}</span>
                <span aria-hidden="true">→</span>
                <span className="report-package__change-new">{replacement}</span>
              </div>
              {(category || reason) && (
                <p className="report-package__change-meta">
                  {category && <span>{category}</span>}
                  {category && reason && <span aria-hidden="true"> · </span>}
                  {reason && <span>{reason}</span>}
                </p>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function ReportEvidenceSection({ evidence }: { evidence: ReportResponse["evidence"] }) {
  if (!evidence || evidence.length === 0) return null;
  return (
    <div className="report-package__section">
      <p className="report-package__section-label">관련 근거 ({evidence.length}건)</p>
      <ul className="report-package__evidence">
        {evidence.map((item, index) => {
          const title = String(item.title ?? "근거 문서");
          const version = item.version ? String(item.version) : "";
          const snippet = item.snippet ? String(item.snippet) : "";
          return (
            <li key={`${title}-${index}`} className="report-package__evidence-item">
              <div className="report-package__evidence-head">
                <span className="report-package__evidence-title">{title}</span>
                {version && <span className="report-package__evidence-version">{version}</span>}
              </div>
              {snippet && <p className="report-package__evidence-snippet">{snippet}</p>}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

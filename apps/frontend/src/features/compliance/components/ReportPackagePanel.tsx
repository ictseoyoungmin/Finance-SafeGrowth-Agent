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

      {helperText ? <p className="report-package__hint">{helperText}</p> : null}
    </section>
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

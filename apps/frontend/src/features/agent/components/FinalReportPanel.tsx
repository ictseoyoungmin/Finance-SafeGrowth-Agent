import type { AgentRunDetail } from "../types";

interface FinalReportPanelProps {
  run?: AgentRunDetail;
  onReset: () => void;
}

export function FinalReportPanel({ run, onReset }: FinalReportPanelProps) {
  if (!run || run.status !== "done") {
    return null;
  }
  const report = run.final_report;

  return (
    <section className="agent-final-panel">
      <div className="panel-heading compact">
        <div>
          <h2>최종 리포트</h2>
          <p>{run.final_summary ?? report?.summary ?? "Agent가 검토를 완료했습니다."}</p>
        </div>
        <span className="run-pill status-done">{decisionLabel(run.final_decision)}</span>
      </div>
      {report ? (
        <div className="agent-final-grid">
          <article>
            <strong>최종 문안</strong>
            <p>{report.final_text}</p>
          </article>
          <article>
            <strong>리스크 수준</strong>
            <p>{report.risk_level ?? "검토 완료"}</p>
          </article>
          <article>
            <strong>근거</strong>
            <p>{report.evidence.length}건 연결</p>
          </article>
        </div>
      ) : null}
      <div className="action-row">
        <button className="secondary-button" onClick={onReset}>처음으로</button>
      </div>
    </section>
  );
}

function decisionLabel(decision?: string | null) {
  const labels: Record<string, string> = {
    approve: "승인",
    reject: "거절",
    revise: "수정 필요",
    none: "판정 없음",
  };
  return labels[decision ?? "none"] ?? "완료";
}

import { useEffect, useState } from "react";

import { ReportPackagePanel } from "./components/ReportPackagePanel";
import { fetchRecentContents, fetchReport } from "./api";
import { approvalDecisionLabel } from "./approvalDecisionLabels";
import type {
  ApprovalDecision,
  RecentContentItem,
  ReportResponse,
} from "./types";

type LoadState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; items: RecentContentItem[] }
  | { status: "error"; message: string };

export function HistoryPage() {
  const [state, setState] = useState<LoadState>({ status: "idle" });
  const [selectedId, setSelectedId] = useState<string | undefined>();
  const [report, setReport] = useState<ReportResponse | undefined>();
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | undefined>();

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });
    fetchRecentContents(20)
      .then((response) => {
        if (cancelled) return;
        setState({ status: "ready", items: response.items });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          message:
            error instanceof Error
              ? error.message
              : "백엔드 응답이 없어 이전 검토를 불러올 수 없습니다.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSelect = (id: string) => {
    setSelectedId(id);
    setReport(undefined);
    setReportError(undefined);
    setReportLoading(true);
    fetchReport(id)
      .then((response) => {
        setReport(response);
        setReportLoading(false);
      })
      .catch((error: unknown) => {
        setReportError(
          error instanceof Error
            ? error.message
            : "리포트를 불러오지 못했습니다.",
        );
        setReportLoading(false);
      });
  };

  return (
    <div className="history-page">
      <header className="panel-heading">
        <h2>검토 이력</h2>
        <p>최근에 저장된 검토 건을 선택해 리포트 패키지를 다시 확인할 수 있습니다.</p>
      </header>

      {state.status === "loading" ? (
        <p className="history-empty" aria-busy>
          최근 검토 목록을 불러오는 중...
        </p>
      ) : null}

      {state.status === "error" ? (
        <div className="notice" role="alert">
          {state.message}
        </div>
      ) : null}

      {state.status === "ready" && state.items.length === 0 ? (
        <p className="history-empty">아직 저장된 검토 건이 없습니다.</p>
      ) : null}

      {state.status === "ready" && state.items.length > 0 ? (
        <ul className="history-list">
          {state.items.map((item) => {
            const isActive = selectedId === item.id;
            return (
              <li key={item.id}>
                <button
                  type="button"
                  className={`history-item ${isActive ? "is-active" : ""}`}
                  onClick={() => handleSelect(item.id)}
                  aria-pressed={isActive}
                >
                  <div className="history-item__head">
                    <span className="history-item__time">
                      {item.created_at ? formatDate(item.created_at) : "시각 정보 없음"}
                    </span>
                    <RiskBadge level={item.risk_level} />
                    <DecisionBadge decision={item.decision} />
                  </div>
                  <p className="history-item__meta">
                    {item.product_type} · {item.channel} · {item.target_customer}
                  </p>
                  <p className="history-item__preview">{item.original_text_preview}</p>
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}

      {selectedId ? (
        <div className="history-report">
          {reportLoading ? (
            <p className="history-empty" aria-busy>
              리포트를 불러오는 중...
            </p>
          ) : null}
          {reportError ? (
            <div className="notice" role="alert">
              {reportError}
            </div>
          ) : null}
          {report ? (
            <ReportPackagePanel
              report={report}
              helperText="좌측 검토 이력에서 다른 건을 선택해 비교할 수 있습니다."
            />
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

function formatDate(value: string): string {
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

interface RiskBadgeProps {
  level?: string | null;
}

function RiskBadge({ level }: RiskBadgeProps) {
  if (!level) return <span className="badge badge--neutral">미분석</span>;
  const className = level === "HIGH" ? "badge--high" : level === "MEDIUM" ? "badge--med" : "badge--low";
  return <span className={`badge ${className}`}>{level}</span>;
}

interface DecisionBadgeProps {
  decision?: ApprovalDecision | string | null;
}

function DecisionBadge({ decision }: DecisionBadgeProps) {
  if (!decision) return <span className="badge badge--neutral">미승인</span>;
  const label = approvalDecisionLabel(decision as ApprovalDecision);
  return <span className="badge badge--decision">{label}</span>;
}

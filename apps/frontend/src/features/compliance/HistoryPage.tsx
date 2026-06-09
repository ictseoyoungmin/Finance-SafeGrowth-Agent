import { useEffect, useState, type MouseEvent } from "react";

import { ArrowLeftIcon } from "../../components/icons";
import { useAuth } from "../auth/AuthContext";
import { ReportPackagePanel } from "./components/ReportPackagePanel";
import {
  deleteAllContents,
  deleteContent,
  fetchRecentContents,
  fetchReport,
} from "./api";
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
  const { profile } = useAuth();
  const canDelete = profile?.role === "admin";
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

  const [deleting, setDeleting] = useState<string | "all" | undefined>();
  const [deleteError, setDeleteError] = useState<string | undefined>();

  const handleDeleteOne = async (id: string, event: MouseEvent) => {
    event.stopPropagation();
    if (!window.confirm("이 검토 건을 삭제할까요? 관련 분석·승인 로그도 함께 삭제됩니다.")) return;
    setDeleting(id);
    setDeleteError(undefined);
    try {
      await deleteContent(id);
      setState((current) =>
        current.status === "ready"
          ? { status: "ready", items: current.items.filter((item) => item.id !== id) }
          : current,
      );
      if (selectedId === id) {
        setSelectedId(undefined);
        setReport(undefined);
      }
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : "삭제에 실패했습니다.");
    } finally {
      setDeleting(undefined);
    }
  };

  const handleDeleteAll = async () => {
    if (!window.confirm("저장된 모든 검토 이력을 삭제할까요? 이 작업은 되돌릴 수 없습니다.")) return;
    setDeleting("all");
    setDeleteError(undefined);
    try {
      await deleteAllContents();
      setState({ status: "ready", items: [] });
      setSelectedId(undefined);
      setReport(undefined);
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : "전체 삭제에 실패했습니다.");
    } finally {
      setDeleting(undefined);
    }
  };

  const handleSelect = (id: string) => {
    if (selectedId === id) {
      setSelectedId(undefined);
      setReport(undefined);
      setReportError(undefined);
      return;
    }
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
      <a className="back-link" href="#/">
        <ArrowLeftIcon size={16} />
        검토로 돌아가기
      </a>

      <header className="panel-heading history-page__head">
        <div>
          <h2>검토 이력</h2>
          <p>최근에 저장된 검토 건을 선택해 리포트 패키지를 다시 확인할 수 있습니다.</p>
        </div>
        {canDelete && state.status === "ready" && state.items.length > 0 ? (
          <button
            type="button"
            className="danger-button"
            onClick={handleDeleteAll}
            disabled={deleting === "all"}
            aria-busy={deleting === "all"}
          >
            {deleting === "all" ? "전체 삭제 중..." : "전체 삭제"}
          </button>
        ) : null}
      </header>

      {deleteError ? (
        <div className="notice" role="alert">
          {deleteError}
        </div>
      ) : null}

      {state.status === "loading" ? (
        <p className="loading-block" aria-busy>
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
              <li key={item.id} className="history-list__item">
                <button
                  type="button"
                  className={`history-item ${isActive ? "is-active" : ""}`}
                  onClick={() => handleSelect(item.id)}
                  aria-expanded={isActive}
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
                {canDelete ? (
                  <button
                    type="button"
                    className="history-item__delete"
                    onClick={(event) => handleDeleteOne(item.id, event)}
                    disabled={deleting === item.id}
                    aria-busy={deleting === item.id}
                    aria-label="이 검토 건 삭제"
                    title="이 검토 건 삭제"
                  >
                    ✕
                  </button>
                ) : null}
                {isActive ? (
                  <div className="history-item__report">
                    {reportLoading ? (
                      <p className="loading-block" aria-busy>
                        리포트 패키지를 불러오는 중...
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
                        helperText="이력에서 다른 건을 선택해 비교하거나, 같은 항목을 다시 눌러 닫을 수 있습니다."
                      />
                    ) : null}
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
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
  return <span className={`badge badge--decision`}>{label}</span>;
}

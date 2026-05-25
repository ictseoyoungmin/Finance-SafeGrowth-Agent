import { useEffect, useRef, useState } from "react";

import { fetchRecentAuditEvents, type RecentAuditEntry } from "../features/compliance/api";

const ACTION_LABELS: Record<string, string> = {
  analyze: "분석 수행",
  evidence: "근거 검색",
  rewrite: "수정안 생성",
  approve: "승인 저장",
  report: "리포트 생성",
};

function actionLabel(action: string): string {
  return ACTION_LABELS[action] ?? action;
}

function formatTime(value?: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

type LoadState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; entries: RecentAuditEntry[] }
  | { status: "error"; message: string };

export function NotificationsBell() {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<LoadState>({ status: "idle" });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setState({ status: "loading" });
    fetchRecentAuditEvents(10)
      .then((response) => {
        if (cancelled) return;
        setState({ status: "ready", entries: response.entries });
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState({
          status: "error",
          message:
            error instanceof Error ? error.message : "알림을 불러오지 못했습니다.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleClick = (event: MouseEvent) => {
      if (!containerRef.current) return;
      if (!containerRef.current.contains(event.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", handleClick);
    return () => window.removeEventListener("mousedown", handleClick);
  }, [open]);

  const count = state.status === "ready" ? state.entries.length : undefined;

  return (
    <div className="notifications" ref={containerRef}>
      <button
        type="button"
        className="notifications__trigger"
        aria-label="알림"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <svg
          width={20}
          height={20}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth={1.8}
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden
        >
          <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
          <path d="M10 21a2 2 0 0 0 4 0" />
        </svg>
        {count !== undefined && count > 0 ? (
          <span className="notifications__badge">{count}</span>
        ) : null}
      </button>

      {open ? (
        <div className="notifications__panel" role="dialog" aria-label="최근 활동">
          <header className="notifications__head">
            <strong>최근 활동</strong>
            <small>최근 audit log 10건</small>
          </header>

          {state.status === "loading" ? (
            <p className="loading-block" aria-busy>알림을 불러오는 중...</p>
          ) : null}
          {state.status === "error" ? (
            <div className="notice" role="alert">{state.message}</div>
          ) : null}
          {state.status === "ready" && state.entries.length === 0 ? (
            <p className="history-empty">아직 활동이 없습니다.</p>
          ) : null}
          {state.status === "ready" && state.entries.length > 0 ? (
            <ul className="notifications__list">
              {state.entries.map((entry, index) => (
                <li key={`${entry.created_at}-${index}`}>
                  <div className="notifications__row">
                    <strong>{actionLabel(entry.action)}</strong>
                    <small>{formatTime(entry.created_at)}</small>
                  </div>
                  <small className="notifications__cid">
                    검토 ID {entry.content_id ? entry.content_id.slice(0, 8) : "—"}
                    {entry.model_version ? ` · ${entry.model_version}` : ""}
                  </small>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

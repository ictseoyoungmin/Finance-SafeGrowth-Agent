import { useEffect, useMemo, useRef, useState } from "react";

import { fetchRecentAuditEvents, type RecentAuditEntry } from "../features/compliance/api";

const ACTION_LABELS: Record<string, string> = {
  analyze: "분석 수행",
  evidence: "근거 검색",
  rewrite: "수정안 생성",
  approve: "승인 저장",
  report: "리포트 생성",
};

const DISMISSED_KEY = "notifications.dismissed.v1";

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

function entryKey(entry: RecentAuditEntry): string {
  return `${entry.created_at ?? ""}::${entry.content_id}::${entry.action}`;
}

function loadDismissed(): Set<string> {
  if (typeof window === "undefined") return new Set();
  try {
    const raw = window.localStorage.getItem(DISMISSED_KEY);
    if (!raw) return new Set();
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? new Set(parsed.filter((v) => typeof v === "string")) : new Set();
  } catch {
    return new Set();
  }
}

function persistDismissed(set: Set<string>) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(DISMISSED_KEY, JSON.stringify(Array.from(set)));
  } catch {
    // ignore
  }
}

type LoadState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; entries: RecentAuditEntry[] }
  | { status: "error"; message: string };

export function NotificationsBell() {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<LoadState>({ status: "idle" });
  const [dismissed, setDismissed] = useState<Set<string>>(() => loadDismissed());
  const containerRef = useRef<HTMLDivElement>(null);

  const loadOnce = (force = false) => {
    if (!force && state.status !== "idle") return;
    setState({ status: "loading" });
    fetchRecentAuditEvents(20)
      .then((response) => {
        setState({ status: "ready", entries: response.entries });
      })
      .catch((error: unknown) => {
        setState({
          status: "error",
          message:
            error instanceof Error ? error.message : "알림을 불러오지 못했습니다.",
        });
      });
  };

  // Initial load — fetch once on mount so the badge shows even before opening
  useEffect(() => {
    loadOnce();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!open) return;
    const handleClick = (event: MouseEvent) => {
      if (!containerRef.current) return;
      if (!containerRef.current.contains(event.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", handleClick);
    return () => window.removeEventListener("mousedown", handleClick);
  }, [open]);

  const visibleEntries = useMemo(() => {
    if (state.status !== "ready") return [];
    return state.entries.filter((entry) => !dismissed.has(entryKey(entry)));
  }, [state, dismissed]);

  const dismissOne = (key: string) => {
    setDismissed((current) => {
      const next = new Set(current);
      next.add(key);
      persistDismissed(next);
      return next;
    });
  };

  const dismissAll = () => {
    setDismissed((current) => {
      const next = new Set(current);
      visibleEntries.forEach((entry) => next.add(entryKey(entry)));
      persistDismissed(next);
      return next;
    });
  };

  const count = visibleEntries.length;

  return (
    <div className="notifications" ref={containerRef}>
      <button
        type="button"
        className="notifications__trigger"
        aria-label="알림"
        aria-expanded={open}
        onClick={() => {
          setOpen((value) => !value);
          loadOnce(true);
        }}
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
        {count > 0 ? <span className="notifications__badge">{count}</span> : null}
      </button>

      {open ? (
        <div className="notifications__panel" role="dialog" aria-label="최근 활동">
          <header className="notifications__head">
            <div>
              <strong>최근 활동</strong>
              <small>읽지 않은 audit log {count}건</small>
            </div>
            {count > 0 ? (
              <button
                type="button"
                className="notifications__action"
                onClick={dismissAll}
              >
                모두 읽음
              </button>
            ) : null}
          </header>

          {state.status === "loading" ? (
            <p className="loading-block" aria-busy>알림을 불러오는 중...</p>
          ) : null}
          {state.status === "error" ? (
            <div className="notice" role="alert">{state.message}</div>
          ) : null}
          {state.status === "ready" && count === 0 ? (
            <p className="history-empty">모두 읽었습니다.</p>
          ) : null}
          {state.status === "ready" && count > 0 ? (
            <ul className="notifications__list">
              {visibleEntries.map((entry) => {
                const key = entryKey(entry);
                return (
                  <li key={key}>
                    <div className="notifications__row">
                      <strong>{actionLabel(entry.action)}</strong>
                      <small>{formatTime(entry.created_at)}</small>
                    </div>
                    <small className="notifications__cid">
                      검토 ID {entry.content_id ? entry.content_id.slice(0, 8) : "—"}
                      {entry.model_version ? ` · ${entry.model_version}` : ""}
                    </small>
                    <button
                      type="button"
                      className="notifications__dismiss"
                      onClick={() => dismissOne(key)}
                      aria-label="이 알림 읽음"
                      title="읽음"
                    >
                      읽음
                    </button>
                  </li>
                );
              })}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

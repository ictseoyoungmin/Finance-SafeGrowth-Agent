import type { ReactNode } from "react";

import type { WorkflowStep } from "../../features/compliance/types";

const STEPS: Array<{ id: WorkflowStep; label: string; icon: string; title: string }> = [
  { id: "input", label: "콘텐츠 입력", icon: "□", title: "콘텐츠 입력" },
  { id: "redline", label: "Redline Risk Review", icon: "○", title: "Redline Risk Review" },
  { id: "evidence", label: "근거 패널", icon: "▤", title: "근거 패널" },
  { id: "rewrite", label: "수정안 비교", icon: "⇄", title: "수정안 비교" },
  { id: "approval", label: "승인 패키지", icon: "▱", title: "승인 패키지" },
];

interface AppShellProps {
  children: ReactNode;
  rightRail?: ReactNode;
  mode?: "agent" | "legacy";
  currentStep?: WorkflowStep;
  apiBaseUrl?: string;
  usedFallback?: boolean;
  errorMessage?: string;
  actionMessage?: string;
}

export function AppShell({
  children,
  rightRail,
  mode = "agent",
  currentStep,
  apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  usedFallback = false,
  errorMessage,
  actionMessage,
}: AppShellProps) {
  const currentTitle =
    mode === "agent"
      ? "AI 규제 Agent 실행"
      : STEPS.find((step) => step.id === currentStep)?.title ?? "콘텐츠 입력";

  return (
    <div className="app-frame">
      <aside className="sidebar" aria-label="workflow steps">
        <div className="brand-block">
          <span className="brand-kicker" aria-hidden="true" />
          <strong>Compliance AI</strong>
        </div>
        <nav className={mode === "agent" ? "step-list app-nav-list" : "step-list"}>
          {mode === "agent" ? (
            <>
              <a className="step-item app-nav-item is-active" href="#/">
                <span>1</span>
                <i aria-hidden="true">◆</i>
                <p>Agent Run</p>
              </a>
              <a className="step-item app-nav-item" href="#/legacy/wizard">
                <span>2</span>
                <i aria-hidden="true">▤</i>
                <p>구버전 5-step 검토</p>
              </a>
            </>
          ) : (
            <>
              <a className="step-item app-nav-item legacy-home" href="#/">
                <span>←</span>
                <i aria-hidden="true">◆</i>
                <p>Agent Run으로</p>
              </a>
              {STEPS.map((step, index) => (
                <div
                  key={step.id}
                  className={`step-item ${step.id === currentStep ? "is-active" : ""}`}
                >
                  <span>{index + 1}</span>
                  <i aria-hidden="true">{step.icon}</i>
                  <p>{step.label}</p>
                </div>
              ))}
            </>
          )}
        </nav>

        <div className="side-card">
          <span className="brand-kicker small" aria-hidden="true" />
          <p>
            {mode === "agent"
              ? "Agent가 규정 검색, 리스크 판단, 수정안 생성, 사람 검토 요청까지 trace로 남깁니다."
              : "AI가 규정·가이드라인 기반으로 리스크를 분석하고 수정안을 제안합니다."}
          </p>
          <strong>자세히 보기 ›</strong>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <h1>{currentTitle}</h1>
          </div>
          <div className="status-stack">
            {actionMessage && !errorMessage ? <span className="topbar-result">{actionMessage}</span> : null}
            <span className="bell">3</span>
            <span className="avatar">A</span>
            <span className="admin-block">
              <strong>Admin</strong>
              <small>준법감시팀</small>
            </span>
            <span className="api-chip">API {apiBaseUrl}</span>
            {usedFallback && <span className="fallback-badge">Fallback</span>}
          </div>
        </header>

        {errorMessage && <div className="notice">{errorMessage}</div>}
        {!errorMessage && actionMessage && <div className="notice success">{actionMessage}</div>}
        {rightRail ? (
          <div className="workspace-with-rail">
            <section className="step-panel">{children}</section>
            {rightRail}
          </div>
        ) : (
          <section className="step-panel">{children}</section>
        )}
      </main>
    </div>
  );
}

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
  currentStep: WorkflowStep;
  apiBaseUrl: string;
  usedFallback: boolean;
  errorMessage?: string;
}

export function AppShell({
  children,
  currentStep,
  apiBaseUrl,
  usedFallback,
  errorMessage,
}: AppShellProps) {
  const currentTitle = STEPS.find((step) => step.id === currentStep)?.title ?? "콘텐츠 입력";

  return (
    <div className="app-frame">
      <aside className="sidebar" aria-label="workflow steps">
        <div className="brand-block">
          <span className="brand-kicker" aria-hidden="true" />
          <strong>Compliance AI</strong>
        </div>
        <nav className="step-list">
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
        </nav>

        <div className="side-card">
          <span className="brand-kicker small" aria-hidden="true" />
          <p>AI가 규정·가이드라인 기반으로 리스크를 분석하고 수정안을 제안합니다.</p>
          <strong>자세히 보기 ›</strong>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <h1>{currentTitle}</h1>
          </div>
          <div className="status-stack">
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
        <section className="step-panel">{children}</section>
      </main>
    </div>
  );
}

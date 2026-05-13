import type { ReactNode } from "react";

import type { WorkflowStep } from "../../features/compliance/types";

const STEPS: Array<{ id: WorkflowStep; label: string }> = [
  { id: "input", label: "콘텐츠 입력" },
  { id: "redline", label: "Redline Risk Review" },
  { id: "evidence", label: "근거 패널" },
  { id: "rewrite", label: "수정안 비교" },
  { id: "approval", label: "승인 패키지" },
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
  return (
    <div className="app-frame">
      <aside className="sidebar" aria-label="workflow steps">
        <div className="brand-block">
          <span className="brand-kicker">JB</span>
          <strong>SafeGrowth Agent</strong>
        </div>
        <nav className="step-list">
          {STEPS.map((step, index) => (
            <div
              key={step.id}
              className={`step-item ${step.id === currentStep ? "is-active" : ""}`}
            >
              <span>{index + 1}</span>
              <p>{step.label}</p>
            </div>
          ))}
        </nav>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Compliance Workspace</p>
            <h1>마케팅 문구 준법 검토</h1>
          </div>
          <div className="status-stack">
            <span>API {apiBaseUrl}</span>
            {usedFallback && <span className="fallback-badge">Fallback</span>}
          </div>
        </header>

        {errorMessage && <div className="notice">{errorMessage}</div>}
        <section className="step-panel">{children}</section>
      </main>
    </div>
  );
}

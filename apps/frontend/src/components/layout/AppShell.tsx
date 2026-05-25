import type { ReactNode } from "react";

import type { WorkflowStep } from "../../features/compliance/types";

const STEPS: Array<{ id: WorkflowStep; label: string; title: string }> = [
  { id: "input", label: "콘텐츠 입력", title: "콘텐츠 입력" },
  { id: "redline", label: "리스크 분석", title: "리스크 분석" },
  { id: "evidence", label: "근거 패널", title: "근거 패널" },
  { id: "rewrite", label: "수정안 비교", title: "수정안 비교" },
  { id: "approval", label: "승인 패키지", title: "승인 패키지" },
];

interface AppShellProps {
  children: ReactNode;
  rightRail?: ReactNode;
  currentStep?: WorkflowStep;
  apiBaseUrl?: string;
  usedFallback?: boolean;
  errorMessage?: string;
  actionMessage?: string;
  isLoading?: boolean;
  title?: string;
}

export function AppShell({
  children,
  rightRail,
  currentStep,
  apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  usedFallback = false,
  errorMessage,
  isLoading = false,
  title,
}: AppShellProps) {
  const currentTitle =
    title ?? STEPS.find((step) => step.id === currentStep)?.title ?? "콘텐츠 입력";

  return (
    <div className="app-frame">
      <aside className="sidebar" aria-label="workflow steps">
        <div className="brand-block">
          <span className="brand-kicker" aria-hidden="true" />
          <strong>준법감시 AI</strong>
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

        <div className="side-foot">
          <a className="side-link" href="#/history">
            <strong>검토 이력</strong>
            <small>DB에 저장된 최근 검토 보기</small>
          </a>
          <div className="side-info-card">
            <p className="side-info-title">규정 기반 검토 가이드</p>
            <p className="side-info-desc">
              리스크 분석은 규정·가이드라인 매칭 결과를 기준으로 진행됩니다. Gemini 응답이 없을 때는
              입력 문장 기반 fallback 으로 작동합니다.
            </p>
            <dl className="side-info-meta">
              <div>
                <dt>API</dt>
                <dd>{apiBaseUrl}</dd>
              </div>
              <div>
                <dt>모드</dt>
                <dd>{usedFallback ? "Fallback" : "Live"}</dd>
              </div>
            </dl>
          </div>
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
              <strong>관리자</strong>
              <small>준법감시팀</small>
            </span>
            <span className="api-chip">API {apiBaseUrl}</span>
            {usedFallback && <span className="fallback-badge">Fallback</span>}
          </div>
          <div
            className={`global-progress ${isLoading ? "is-active" : ""}`}
            aria-hidden={!isLoading}
            role="progressbar"
            aria-busy={isLoading}
          >
            <span />
          </div>
        </header>

        {errorMessage && <div className="notice">{errorMessage}</div>}
        {rightRail ? (
          <div className="workspace-with-rail">
            <section className={`step-panel ${isLoading ? "is-busy" : ""}`}>{children}</section>
            {rightRail}
          </div>
        ) : (
          <section className={`step-panel ${isLoading ? "is-busy" : ""}`}>{children}</section>
        )}
      </main>
    </div>
  );
}

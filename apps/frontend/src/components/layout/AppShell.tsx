import { useState, type ComponentType, type ReactNode, type SVGProps } from "react";

import type { WorkflowStep } from "../../features/compliance/types";
import {
  ApproveIcon,
  ArchiveIcon,
  ChevronIcon,
  CompareIcon,
  DocumentIcon,
  EvidenceIcon,
  RiskIcon,
} from "../icons";
import { NotificationsBell } from "../NotificationsBell";

type IconComponent = ComponentType<SVGProps<SVGSVGElement> & { size?: number }>;

const STEPS: Array<{ id: WorkflowStep; label: string; title: string; Icon: IconComponent }> = [
  { id: "input", label: "콘텐츠 입력", title: "콘텐츠 입력", Icon: DocumentIcon },
  { id: "redline", label: "리스크 분석", title: "리스크 분석", Icon: RiskIcon },
  { id: "evidence", label: "근거 패널", title: "근거 패널", Icon: EvidenceIcon },
  { id: "rewrite", label: "수정안 비교", title: "수정안 비교", Icon: CompareIcon },
  { id: "approval", label: "승인 패키지", title: "승인 패키지", Icon: ApproveIcon },
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
  onNavigateStep?: (step: WorkflowStep) => void;
  availableSteps?: ReadonlySet<WorkflowStep>;
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
  onNavigateStep,
  availableSteps,
}: AppShellProps) {
  const [guideOpen, setGuideOpen] = useState(false);
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
          {STEPS.map((step, index) => {
            const Icon = step.Icon;
            const isActive = step.id === currentStep;
            const navigable =
              Boolean(onNavigateStep) && (availableSteps?.has(step.id) ?? false);
            const className = `step-item ${isActive ? "is-active" : ""} ${
              navigable ? "is-navigable" : ""
            }`;
            const inner = (
              <>
                <span>{index + 1}</span>
                <Icon className="step-item__icon" />
                <p>{step.label}</p>
              </>
            );
            if (!navigable) {
              return (
                <div key={step.id} className={className} aria-current={isActive ? "step" : undefined}>
                  {inner}
                </div>
              );
            }
            return (
              <button
                key={step.id}
                type="button"
                className={className}
                aria-current={isActive ? "step" : undefined}
                onClick={() => onNavigateStep?.(step.id)}
              >
                {inner}
              </button>
            );
          })}
        </nav>

        <div className="side-foot">
          <a className="side-link" href="#/history">
            <ArchiveIcon className="side-link__icon" size={20} />
            <div>
              <strong>검토 이력</strong>
              <small>DB에 저장된 최근 검토 보기</small>
            </div>
          </a>
          <div className={`side-guide ${guideOpen ? "is-open" : ""}`}>
            <button
              type="button"
              className="side-guide__toggle"
              aria-expanded={guideOpen}
              onClick={() => setGuideOpen((open) => !open)}
            >
              <span>규정 기반 검토 가이드</span>
              <ChevronIcon className="side-guide__chevron" size={16} />
            </button>
            {guideOpen ? (
              <div className="side-guide__body">
                <p className="side-guide__desc">
                  리스크 분석은 규정·가이드라인 매칭 결과를 기준으로 진행됩니다. Gemini 응답이
                  없을 때는 입력 문장 기반 fallback 으로 작동합니다.
                </p>
                <dl className="side-guide__meta">
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
            ) : null}
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <h1>{currentTitle}</h1>
          </div>
          <div className="status-stack">
            <NotificationsBell />
            <span className="avatar">A</span>
            <span className="admin-block">
              <strong>관리자</strong>
              <small>준법감시팀</small>
            </span>
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

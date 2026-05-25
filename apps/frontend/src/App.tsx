import { useEffect, useState } from "react";

import { AppShell } from "./components/layout/AppShell";
import { AgentRunPage } from "./features/agent/AgentRunPage";
import { ComplianceTraceRail } from "./features/compliance/components/ComplianceTraceRail";
import { HistoryPage } from "./features/compliance/HistoryPage";
import { useComplianceWorkflow } from "./features/compliance/store";
import { ApprovalStep } from "./features/compliance/steps/ApprovalStep";
import { EvidenceStep } from "./features/compliance/steps/EvidenceStep";
import { InputStep } from "./features/compliance/steps/InputStep";
import { RedlineStep } from "./features/compliance/steps/RedlineStep";
import { RewriteStep } from "./features/compliance/steps/RewriteStep";
import type { WorkflowStep } from "./features/compliance/types";

export function App() {
  const route = useHashRoute();

  if (route === "/agent") {
    return (
      <AppShell>
        <AgentRunPage />
      </AppShell>
    );
  }

  if (route === "/history") {
    return (
      <AppShell title="검토 이력">
        <HistoryPage />
      </AppShell>
    );
  }

  return <ComplianceWizard />;
}

function ComplianceWizard() {
  const workflow = useComplianceWorkflow();
  const { state } = workflow;
  const availableSteps = new Set<WorkflowStep>(["input"]);
  if (state.analyze) availableSteps.add("redline");
  if (state.evidence) availableSteps.add("evidence");
  if (state.rewrite) availableSteps.add("rewrite");
  if (state.approval || state.step === "approval") availableSteps.add("approval");

  return (
    <AppShell
      currentStep={workflow.state.step}
      apiBaseUrl={workflow.apiBaseUrl}
      usedFallback={workflow.state.usedFallback}
      errorMessage={workflow.state.errorMessage}
      actionMessage={workflow.state.actionMessage}
      isLoading={workflow.state.isLoading}
      onNavigateStep={workflow.goTo}
      availableSteps={availableSteps}
      rightRail={<ComplianceTraceRail workflow={workflow} />}
    >
      {workflow.state.step === "input" && <InputStep workflow={workflow} />}
      {workflow.state.step === "redline" && <RedlineStep workflow={workflow} />}
      {workflow.state.step === "evidence" && <EvidenceStep workflow={workflow} />}
      {workflow.state.step === "rewrite" && <RewriteStep workflow={workflow} />}
      {workflow.state.step === "approval" && <ApprovalStep workflow={workflow} />}
    </AppShell>
  );
}

function useHashRoute() {
  const getRoute = () => window.location.hash.replace(/^#/, "") || "/";
  const [route, setRoute] = useState(getRoute);

  useEffect(() => {
    const handleHashChange = () => setRoute(getRoute());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  return route;
}

import { useEffect, useState } from "react";

import { AppShell } from "./components/layout/AppShell";
import { AgentRunPage } from "./features/agent/AgentRunPage";
import { useComplianceWorkflow } from "./features/compliance/store";
import { ApprovalStep } from "./features/compliance/steps/ApprovalStep";
import { EvidenceStep } from "./features/compliance/steps/EvidenceStep";
import { InputStep } from "./features/compliance/steps/InputStep";
import { RedlineStep } from "./features/compliance/steps/RedlineStep";
import { RewriteStep } from "./features/compliance/steps/RewriteStep";

export function App() {
  const route = useHashRoute();

  if (route === "/legacy/wizard") {
    return <LegacyWizard />;
  }

  return (
    <AppShell mode="agent">
      <AgentRunPage />
    </AppShell>
  );
}

function LegacyWizard() {
  const workflow = useComplianceWorkflow();

  return (
    <AppShell
      mode="legacy"
      currentStep={workflow.state.step}
      apiBaseUrl={workflow.apiBaseUrl}
      usedFallback={workflow.state.usedFallback}
      errorMessage={workflow.state.errorMessage}
      actionMessage={workflow.state.actionMessage}
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

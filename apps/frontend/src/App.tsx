import { AppShell } from "./components/layout/AppShell";
import { useComplianceWorkflow } from "./features/compliance/store";
import { ApprovalStep } from "./features/compliance/steps/ApprovalStep";
import { EvidenceStep } from "./features/compliance/steps/EvidenceStep";
import { InputStep } from "./features/compliance/steps/InputStep";
import { RedlineStep } from "./features/compliance/steps/RedlineStep";
import { RewriteStep } from "./features/compliance/steps/RewriteStep";

export function App() {
  const workflow = useComplianceWorkflow();

  return (
    <AppShell
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

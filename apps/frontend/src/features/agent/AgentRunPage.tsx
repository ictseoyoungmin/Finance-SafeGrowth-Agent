import { useCallback } from "react";

import { useAgentRunStream } from "./hooks/useAgentRunStream";
import { useAgentWorkflow } from "./store";
import { FinalReportPanel } from "./components/FinalReportPanel";
import { HumanReviewPanel } from "./components/HumanReviewPanel";
import { InputForm } from "./components/InputForm";
import { StepDetailPanel } from "./components/StepDetailPanel";
import { TraceTimeline } from "./components/TraceTimeline";
import type { AgentRunDetail } from "./types";

export function AgentRunPage() {
  const workflow = useAgentWorkflow();
  const { refreshRun } = workflow;
  const handleUpdate = useCallback((detail: AgentRunDetail) => refreshRun(detail), [refreshRun]);
  useAgentRunStream(workflow.runDetail?.id, handleUpdate);

  return (
    <div className="agent-run-page">
      {workflow.errorMessage ? <div className="notice">{workflow.errorMessage}</div> : null}
      <InputForm workflow={workflow} />
      <div className="agent-run-grid">
        <TraceTimeline
          steps={workflow.runDetail?.steps ?? []}
          selected={workflow.selectedStep}
          onSelect={workflow.selectStep}
        />
        <StepDetailPanel step={workflow.selectedStep} />
      </div>
      <HumanReviewPanel workflow={workflow} />
      <FinalReportPanel run={workflow.runDetail} onReset={workflow.reset} />
    </div>
  );
}

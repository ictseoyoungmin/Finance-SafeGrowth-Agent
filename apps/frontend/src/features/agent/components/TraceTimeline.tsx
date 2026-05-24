import type { AgentStep } from "../types";
import { traceSubtitle, traceTitle, traceTypeLabel } from "../tracePresentation";

interface TraceTimelineProps {
  steps: AgentStep[];
  selected?: AgentStep;
  onSelect: (step: AgentStep) => void;
}

export function TraceTimeline({ steps, selected, onSelect }: TraceTimelineProps) {
  return (
    <section className="trace-timeline">
      <div className="panel-heading compact">
        <div>
          <h2>실행 Trace</h2>
          <p>{steps.length ? `${steps.length}개 이벤트` : "Agent 실행 후 이벤트가 표시됩니다."}</p>
        </div>
      </div>
      <div className="trace-list">
        {steps.map((step) => (
          <button
            key={`${step.run_id}-${step.step_index}`}
            className={`trace-item ${selected?.step_index === step.step_index ? "is-selected" : ""} step-${step.step_type}`}
            onClick={() => onSelect(step)}
            aria-current={selected?.step_index === step.step_index ? "step" : undefined}
          >
            <span>{stepIcon(step)}</span>
            <div>
              <em>{traceTypeLabel(step.step_type)}</em>
              <strong>{traceTitle(step)}</strong>
              <small>{traceSubtitle(step)}</small>
            </div>
            <time>{step.created_at ? new Date(step.created_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }) : `#${step.step_index}`}</time>
          </button>
        ))}
      </div>
    </section>
  );
}

function stepIcon(step: AgentStep) {
  if (step.step_type === "tool_call") return "◇";
  if (step.step_type === "tool_result") return "◆";
  if (step.step_type === "human_prompt") return "!";
  if (step.step_type === "human_response") return "↵";
  if (step.step_type === "final") return "✓";
  return "•";
}

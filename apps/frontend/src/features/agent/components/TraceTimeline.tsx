import type { AgentStep } from "../types";

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
              <em>{stepTypeLabel(step.step_type)}</em>
              <strong>{stepTitle(step)}</strong>
            </div>
            <small>{step.created_at ? new Date(step.created_at).toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" }) : `#${step.step_index}`}</small>
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

function stepTitle(step: AgentStep) {
  if (step.tool_name) return step.tool_name;
  const labels: Record<string, string> = {
    thought: "생각",
    human_prompt: "사람 검토 요청",
    human_response: "사람 응답",
    final: "최종 결과",
  };
  return labels[step.step_type] ?? step.step_type;
}

function stepTypeLabel(type: string) {
  const labels: Record<string, string> = {
    thought: "관찰",
    tool_call: "도구 호출",
    tool_result: "도구 결과",
    human_prompt: "사람 확인 요청",
    human_response: "사람 응답",
    final: "최종 결과",
  };
  return labels[type] ?? type;
}

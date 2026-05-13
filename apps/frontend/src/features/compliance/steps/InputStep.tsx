import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function InputStep({ workflow }: StepProps) {
  const { state, updateInput, startReview } = workflow;

  return (
    <div className="step-grid">
      <div className="form-stack">
        <label>
          상품 유형
          <input
            value={state.input.product_type}
            onChange={(event) => updateInput({ product_type: event.target.value })}
          />
        </label>
        <label>
          채널
          <input
            value={state.input.channel}
            onChange={(event) => updateInput({ channel: event.target.value })}
          />
        </label>
        <label>
          대상 고객
          <input
            value={state.input.target_customer}
            onChange={(event) => updateInput({ target_customer: event.target.value })}
          />
        </label>
      </div>

      <label className="copy-field">
        검토 문구
        <textarea
          rows={8}
          value={state.input.original_text}
          onChange={(event) => updateInput({ original_text: event.target.value })}
        />
      </label>

      <div className="action-row">
        <button className="primary-button" onClick={startReview} disabled={state.isLoading}>
          {state.isLoading ? "검토 중" : "준법검토 시작"}
        </button>
      </div>
    </div>
  );
}

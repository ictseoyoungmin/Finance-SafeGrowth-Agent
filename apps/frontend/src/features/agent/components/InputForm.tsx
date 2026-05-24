import type { AgentWorkflow } from "../store";

interface InputFormProps {
  workflow: AgentWorkflow;
}

export function InputForm({ workflow }: InputFormProps) {
  const { draft, isLoading, runDetail, start, updateDraft, cancel, reset } = workflow;
  const compact = Boolean(runDetail);

  return (
    <section className={`agent-input ${compact ? "is-compact" : ""}`}>
      <div className="panel-heading compact">
        <div>
          <h2>Agent 실행 입력</h2>
          <p>광고 문안을 입력하면 AI Agent가 필요한 도구를 선택해 검토합니다.</p>
        </div>
        {runDetail ? <span className={`run-pill status-${runDetail.status}`}>{statusLabel(runDetail.status)}</span> : null}
      </div>

      <div className="agent-input-grid">
        <label>
          <span>제품 유형</span>
          <input value={draft.product_type ?? ""} onChange={(event) => updateDraft({ product_type: event.target.value })} />
        </label>
        <label>
          <span>채널</span>
          <input value={draft.channel ?? ""} onChange={(event) => updateDraft({ channel: event.target.value })} />
        </label>
        <label>
          <span>대상 고객</span>
          <input
            value={draft.target_customer ?? ""}
            onChange={(event) => updateDraft({ target_customer: event.target.value })}
          />
        </label>
        <label>
          <span>실행 모드</span>
          <select
            value={draft.mode}
            onChange={(event) => updateDraft({ mode: event.target.value as "review" | "rewrite_only" | "explain" })}
          >
            <option value="review">준법 검토</option>
            <option value="rewrite_only">수정안 중심</option>
            <option value="explain">설명 중심</option>
          </select>
        </label>
      </div>
      <label>
        <span>검토 문안</span>
        <textarea value={draft.text ?? ""} onChange={(event) => updateDraft({ text: event.target.value })} />
      </label>

      <div className="action-row">
        {runDetail ? (
          <>
            <button className="secondary-button" onClick={reset}>새 실행</button>
            <button className="danger-button" onClick={cancel} disabled={isLoading || ["done", "failed", "cancelled"].includes(runDetail.status)}>
              실행 취소
            </button>
          </>
        ) : null}
        <button className="primary-button" onClick={start} disabled={isLoading || !draft.text?.trim()}>
          Agent 실행
        </button>
      </div>
    </section>
  );
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    running: "실행 중",
    awaiting_human: "사람 검토 대기",
    done: "완료",
    failed: "실패",
    cancelled: "취소됨",
  };
  return labels[status] ?? status;
}

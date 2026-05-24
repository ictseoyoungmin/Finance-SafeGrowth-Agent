import { useState } from "react";

import type { AgentWorkflow } from "../store";

interface HumanReviewPanelProps {
  workflow: AgentWorkflow;
}

export function HumanReviewPanel({ workflow }: HumanReviewPanelProps) {
  const prompt = workflow.runDetail?.pending_human;
  const [freeText, setFreeText] = useState("");
  const [pendingOption, setPendingOption] = useState<string | undefined>();

  if (!prompt || workflow.runDetail?.status !== "awaiting_human") {
    return null;
  }

  const options = prompt.options?.length ? prompt.options : ["approve", "revise", "reject"];

  return (
    <section className="human-review-panel">
      <div>
        <h2>사람 검토 필요</h2>
        <p>{prompt.question}</p>
      </div>
      <div className="human-option-row">
        {options.map((option) => {
          const isPending = workflow.isLoading && pendingOption === option;
          return (
            <button
              key={option}
              className="choice-button"
              onClick={() => {
                setPendingOption(option);
                void workflow.respond(option).finally(() => setPendingOption(undefined));
              }}
              disabled={workflow.isLoading}
              aria-busy={isPending}
            >
              {isPending ? `${optionLabel(option)} 처리 중...` : optionLabel(option)}
            </button>
          );
        })}
      </div>
      <div className="human-freeform">
        <input value={freeText} onChange={(event) => setFreeText(event.target.value)} placeholder="추가 지시 입력" />
        <button
          className="secondary-button"
          onClick={() => {
            setPendingOption("freeform");
            void workflow.respond(freeText).finally(() => setPendingOption(undefined));
          }}
          disabled={!freeText.trim() || workflow.isLoading}
          aria-busy={workflow.isLoading && pendingOption === "freeform"}
        >
          {workflow.isLoading && pendingOption === "freeform" ? "지시 제출 중..." : "지시 제출"}
        </button>
      </div>
    </section>
  );
}

function optionLabel(option: string) {
  const labels: Record<string, string> = {
    approve: "승인",
    reject: "거절",
    revise: "수정 요청",
  };
  return labels[option] ?? option;
}

import type { FlaggedSpan } from "./types";

const CATEGORY_LABELS: Record<string, string> = {
  guaranteed_return: "확정 수익처럼 보일 수 있는 표현입니다.",
  principal_guarantee: "원금 보장으로 오인될 수 있는 표현입니다.",
  exaggerated_safety: "투자 위험이 낮거나 없다는 인상을 줄 수 있습니다.",
  misleading_targeting: "대상 고객에게 상품 적합성을 과도하게 암시할 수 있습니다.",
  missing_risk_notice: "손실 가능성이나 유의사항 고지가 부족합니다.",
  promotion_condition: "이벤트 조건·기간·대상 범위 확인이 필요합니다.",
};

export function riskReasonKo(span?: FlaggedSpan) {
  if (!span) return "표준 데모 문구";
  return CATEGORY_LABELS[span.risk_category] ?? translateReason(span.reason);
}

export function riskCategoryKo(category?: string) {
  if (!category) return "검토 필요";
  return CATEGORY_LABELS[category]?.replace("입니다.", "") ?? category;
}

export function sourceLabel(source?: FlaggedSpan["source"]) {
  if (source === "gemini") return "Gemini";
  if (source === "llm") return "LLM";
  return "규칙";
}

function translateReason(reason?: string) {
  if (!reason) return "문구의 규제 적합성 확인이 필요합니다.";
  const lowered = reason.toLowerCase();
  if (lowered.includes("guarantee") || lowered.includes("principal")) {
    return "원금 또는 성과 보장으로 해석될 수 있어 확인이 필요합니다.";
  }
  if (lowered.includes("return") || lowered.includes("profit")) {
    return "수익률을 확정적으로 제시한 표현인지 확인이 필요합니다.";
  }
  if (lowered.includes("risk") || lowered.includes("safe")) {
    return "위험 고지와 안전성 표현의 균형을 확인해야 합니다.";
  }
  return "규정 문맥에 맞게 표현 수위를 확인해야 합니다.";
}

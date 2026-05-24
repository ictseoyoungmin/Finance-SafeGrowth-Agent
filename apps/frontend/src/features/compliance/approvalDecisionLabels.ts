import type { ApprovalDecision } from "./types";

export const APPROVAL_DECISION_LABELS: Record<ApprovalDecision, string> = {
  APPROVED: "승인",
  CONDITIONALLY_APPROVED: "조건부 승인",
  REJECTED: "반려",
  REVISION_REQUESTED: "수정 요청",
};

export function approvalDecisionLabel(decision?: ApprovalDecision | null) {
  return decision ? APPROVAL_DECISION_LABELS[decision] : "조건부 승인 권고";
}

export function replaceApprovalDecisionCodes(text?: string | null) {
  if (!text) return text;
  return (Object.entries(APPROVAL_DECISION_LABELS) as Array<[ApprovalDecision, string]>).reduce(
    (current, [code, label]) => current.split(code).join(label),
    text,
  );
}

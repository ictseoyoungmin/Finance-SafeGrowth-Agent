import { useEffect, useMemo, useState } from "react";

import {
  DEFAULT_INPUT,
  analyzeContent,
  approveContent,
  fallbackAnalyze,
  fallbackEvidence,
  fallbackRewrite,
  fetchEvidence,
  fetchReport,
  fetchRewrite,
  getApiBaseUrl,
} from "./api";
import { approvalDecisionLabel } from "./approvalDecisionLabels";
import type { AnalyzeRequest, ApprovalDecision, ComplianceState, WorkflowStep } from "./types";

export interface ComplianceWorkflow {
  state: ComplianceState;
  apiBaseUrl: string;
  updateInput: (patch: Partial<AnalyzeRequest>) => void;
  startReview: () => Promise<void>;
  loadEvidence: () => Promise<void>;
  loadRewrite: () => Promise<void>;
  submitApproval: (decision: ApprovalDecision) => Promise<void>;
  loadReport: () => Promise<void>;
  selectRevision: (revision: ComplianceState["selectedRevision"]) => void;
  goTo: (step: WorkflowStep) => void;
  reset: () => void;
}

const INITIAL_STATE: ComplianceState = {
  step: "input",
  input: DEFAULT_INPUT,
  selectedRevision: "marketing",
  usedFallback: false,
  isLoading: false,
};

const STORAGE_KEY = "compliance.workflow.v1";

function loadPersisted(): ComplianceState | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<ComplianceState>;
    if (!parsed || typeof parsed !== "object" || !parsed.input) return null;
    return {
      ...INITIAL_STATE,
      ...parsed,
      // always reset volatile flags on reload
      isLoading: false,
      pendingAction: undefined,
      errorMessage: undefined,
      actionMessage: undefined,
    } as ComplianceState;
  } catch {
    return null;
  }
}

function persist(state: ComplianceState) {
  if (typeof window === "undefined") return;
  try {
    const { isLoading: _il, pendingAction: _pa, errorMessage: _em, actionMessage: _am, ...persistable } = state;
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(persistable));
  } catch {
    // quota or serialization issues — silently ignore
  }
}

function clearPersisted() {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

function pendingActionForDecision(decision: ApprovalDecision): ComplianceState["pendingAction"] {
  if (decision === "REJECTED") return "reject";
  if (decision === "REVISION_REQUESTED") return "request_revision";
  return "approve";
}

export function useComplianceWorkflow(): ComplianceWorkflow {
  const [state, setState] = useState<ComplianceState>(() => loadPersisted() ?? INITIAL_STATE);
  const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);

  useEffect(() => {
    persist(state);
  }, [state]);

  const updateInput = (patch: Partial<AnalyzeRequest>) => {
    setState((current) => ({
      ...current,
      input: { ...current.input, ...patch },
      errorMessage: undefined,
    }));
  };

  const startReview = async () => {
    setState((current) => ({
      ...current,
      isLoading: true,
      pendingAction: undefined,
      errorMessage: undefined,
      actionMessage: undefined,
    }));
    try {
      const analyze = await analyzeContent(state.input);
      setState((current) => ({
        ...current,
        step: "redline",
        analyze,
        isLoading: false,
        actionMessage: undefined,
      }));
    } catch {
      const analyze = fallbackAnalyze(state.input);
      setState((current) => ({
        ...current,
        step: "redline",
        analyze,
        usedFallback: true,
        isLoading: false,
        errorMessage: "백엔드 응답이 없어 데모 fallback으로 검토를 진행합니다.",
        actionMessage: undefined,
      }));
    }
  };

  const loadEvidence = async () => {
    const analyze = state.analyze ?? fallbackAnalyze(state.input);
    setState((current) => ({
      ...current,
      isLoading: true,
      pendingAction: undefined,
      errorMessage: undefined,
      actionMessage: undefined,
    }));
    try {
      const evidence = await fetchEvidence({
        content_id: analyze.content_id,
        risk_categories: analyze.risk_categories,
        product_type: state.input.product_type,
      });
      setState((current) => ({
        ...current,
        step: "evidence",
        evidence,
        isLoading: false,
        actionMessage: undefined,
      }));
    } catch {
      setState((current) => ({
        ...current,
        step: "evidence",
        evidence: fallbackEvidence(analyze.content_id),
        usedFallback: true,
        isLoading: false,
        errorMessage: "근거 API 응답이 없어 데모 근거를 표시합니다.",
        actionMessage: undefined,
      }));
    }
  };

  const loadRewrite = async () => {
    const contentId = state.analyze?.content_id ?? "demo-content";
    setState((current) => ({
      ...current,
      isLoading: true,
      pendingAction: undefined,
      errorMessage: undefined,
      actionMessage: undefined,
    }));
    try {
      const rewrite = await fetchRewrite({ content_id: contentId, mode: "marketing_balanced" });
      const rewriteUsedFallback = rewrite.source === "fallback";
      setState((current) => ({
        ...current,
        step: "rewrite",
        rewrite,
        usedFallback: current.usedFallback || rewriteUsedFallback,
        isLoading: false,
        actionMessage: rewriteUsedFallback
          ? "Gemini 응답 대신 입력 문장 기반 deterministic fallback 수정안을 표시합니다."
          : "Gemini 검수 수정안을 불러왔습니다.",
      }));
    } catch {
      setState((current) => ({
        ...current,
        step: "rewrite",
        rewrite: fallbackRewrite(contentId),
        usedFallback: true,
        isLoading: false,
        errorMessage: "수정안 API 응답이 없어 데모 수정안을 표시합니다.",
        actionMessage: undefined,
      }));
    }
  };

  const submitApproval = async (decision: ApprovalDecision) => {
    const contentId = state.analyze?.content_id ?? "demo-content";
    const selectedRevisionText =
      state.selectedRevision === "conservative"
        ? state.rewrite?.revised_text_conservative
        : state.rewrite?.revised_text_marketing;
    setState((current) => ({
      ...current,
      isLoading: true,
      pendingAction: pendingActionForDecision(decision),
      errorMessage: undefined,
      actionMessage: `${approvalDecisionLabel(decision)} 저장 중...`,
    }));
    try {
      const approval = await approveContent({
        content_id: contentId,
        reviewer: "김준법 수석",
        decision,
        comment: decision === "CONDITIONALLY_APPROVED" ? "Demo approval" : undefined,
        selected_revision: selectedRevisionText ?? state.input.original_text,
      });
      setState((current) => ({
        ...current,
        approval,
        isLoading: false,
        pendingAction: undefined,
        actionMessage: `${approvalDecisionLabel(approval.decision)}으로 저장되었습니다.`,
      }));
    } catch {
      setState((current) => ({
        ...current,
        usedFallback: true,
        isLoading: false,
        pendingAction: undefined,
        errorMessage: "승인 저장에 실패했습니다. 다시 시도해주세요.",
      }));
    }
  };

  const loadReport = async () => {
    const contentId = state.analyze?.content_id ?? "demo-content";
    setState((current) => ({
      ...current,
      isLoading: true,
      pendingAction: "load_report",
      errorMessage: undefined,
    }));
    try {
      const report = await fetchReport(contentId);
      setState((current) => ({
        ...current,
        report,
        isLoading: false,
        pendingAction: undefined,
        actionMessage: "리포트 패키지를 불러왔습니다.",
      }));
    } catch {
      setState((current) => ({
        ...current,
        usedFallback: true,
        isLoading: false,
        pendingAction: undefined,
        errorMessage: "리포트 API 응답이 없어 현재 화면 데이터로 검토를 이어갑니다.",
      }));
    }
  };

  const goTo = (step: WorkflowStep) => {
    setState((current) => ({ ...current, step, errorMessage: undefined }));
  };

  const selectRevision = (revision: ComplianceState["selectedRevision"]) => {
    setState((current) => ({ ...current, selectedRevision: revision }));
  };

  const reset = () => {
    clearPersisted();
    setState(INITIAL_STATE);
  };

  return {
    state,
    apiBaseUrl,
    updateInput,
    startReview,
    loadEvidence,
    loadRewrite,
    submitApproval,
    loadReport,
    selectRevision,
    goTo,
    reset,
  };
}

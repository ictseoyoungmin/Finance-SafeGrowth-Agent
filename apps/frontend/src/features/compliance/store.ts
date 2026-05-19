import { useMemo, useState } from "react";

import {
  DEFAULT_INPUT,
  analyzeContent,
  fallbackAnalyze,
  fallbackEvidence,
  fallbackRewrite,
  fetchEvidence,
  fetchRewrite,
  getApiBaseUrl,
} from "./api";
import type { AnalyzeRequest, ComplianceState, WorkflowStep } from "./types";

export interface ComplianceWorkflow {
  state: ComplianceState;
  apiBaseUrl: string;
  updateInput: (patch: Partial<AnalyzeRequest>) => void;
  startReview: () => Promise<void>;
  loadEvidence: () => Promise<void>;
  loadRewrite: () => Promise<void>;
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

export function useComplianceWorkflow(): ComplianceWorkflow {
  const [state, setState] = useState<ComplianceState>(INITIAL_STATE);
  const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);

  const updateInput = (patch: Partial<AnalyzeRequest>) => {
    setState((current) => ({
      ...current,
      input: { ...current.input, ...patch },
      errorMessage: undefined,
    }));
  };

  const startReview = async () => {
    setState((current) => ({ ...current, isLoading: true, errorMessage: undefined }));
    try {
      const analyze = await analyzeContent(state.input);
      setState((current) => ({
        ...current,
        step: "redline",
        analyze,
        isLoading: false,
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
      }));
    }
  };

  const loadEvidence = async () => {
    const analyze = state.analyze ?? fallbackAnalyze(state.input);
    setState((current) => ({ ...current, isLoading: true, errorMessage: undefined }));
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
      }));
    } catch {
      setState((current) => ({
        ...current,
        step: "evidence",
        evidence: fallbackEvidence(analyze.content_id),
        usedFallback: true,
        isLoading: false,
        errorMessage: "근거 API 응답이 없어 데모 근거를 표시합니다.",
      }));
    }
  };

  const loadRewrite = async () => {
    const contentId = state.analyze?.content_id ?? "demo-content";
    setState((current) => ({ ...current, isLoading: true, errorMessage: undefined }));
    try {
      const rewrite = await fetchRewrite({ content_id: contentId, mode: "marketing_balanced" });
      setState((current) => ({
        ...current,
        step: "rewrite",
        rewrite,
        isLoading: false,
      }));
    } catch {
      setState((current) => ({
        ...current,
        step: "rewrite",
        rewrite: fallbackRewrite(contentId),
        usedFallback: true,
        isLoading: false,
        errorMessage: "수정안 API 응답이 없어 데모 수정안을 표시합니다.",
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
    setState(INITIAL_STATE);
  };

  return {
    state,
    apiBaseUrl,
    updateInput,
    startReview,
    loadEvidence,
    loadRewrite,
    selectRevision,
    goTo,
    reset,
  };
}

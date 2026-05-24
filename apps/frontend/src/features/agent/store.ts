import { useCallback, useMemo, useState } from "react";

import { DEMO_TEXT, getApiBaseUrl } from "../compliance/api";
import { cancelAgentRun, respondAgentRun, startAgentRun } from "./api";
import type { AgentRunDetail, AgentRunRequest, AgentStep } from "./types";

export interface AgentWorkflow {
  apiBaseUrl: string;
  draft: AgentRunRequest;
  runDetail?: AgentRunDetail;
  selectedStep?: AgentStep;
  isLoading: boolean;
  errorMessage?: string;
  updateDraft: (patch: Partial<AgentRunRequest>) => void;
  start: () => Promise<void>;
  respond: (response: unknown) => Promise<void>;
  cancel: () => Promise<void>;
  selectStep: (step: AgentStep) => void;
  refreshRun: (detail: AgentRunDetail) => void;
  reset: () => void;
}

const INITIAL_DRAFT: AgentRunRequest = {
  text: DEMO_TEXT,
  mode: "review",
  product_type: "투자상품",
  channel: "앱 푸시",
  target_customer: "30대 직장인",
  language: "ko",
};

export function useAgentWorkflow(): AgentWorkflow {
  const [draft, setDraft] = useState<AgentRunRequest>(INITIAL_DRAFT);
  const [runDetail, setRunDetail] = useState<AgentRunDetail | undefined>();
  const [selectedStepIndex, setSelectedStepIndex] = useState<number | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | undefined>();
  const apiBaseUrl = useMemo(() => getApiBaseUrl(), []);

  const selectedStep =
    runDetail?.steps.find((step) => step.step_index === selectedStepIndex) ??
    runDetail?.steps[runDetail.steps.length - 1];

  const updateDraft = (patch: Partial<AgentRunRequest>) => {
    setDraft((current) => ({ ...current, ...patch }));
    setErrorMessage(undefined);
  };

  const refreshRun = useCallback((detail: AgentRunDetail) => {
    setRunDetail(detail);
    if (selectedStepIndex === undefined && detail.steps.length) {
      setSelectedStepIndex(detail.steps[detail.steps.length - 1].step_index);
    }
  }, [selectedStepIndex]);

  const start = async () => {
    setIsLoading(true);
    setErrorMessage(undefined);
    try {
      const detail = await startAgentRun(draft);
      setRunDetail(detail);
      setSelectedStepIndex(detail.steps[detail.steps.length - 1]?.step_index);
    } catch {
      setErrorMessage("Agent 실행을 시작하지 못했습니다. 백엔드 상태를 확인해 주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  const respond = async (response: unknown) => {
    if (!runDetail) return;
    setIsLoading(true);
    setErrorMessage(undefined);
    try {
      const detail = await respondAgentRun(runDetail.id, response);
      setRunDetail(detail);
      setSelectedStepIndex(detail.steps[detail.steps.length - 1]?.step_index);
    } catch {
      setErrorMessage("응답을 제출하지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const cancel = async () => {
    if (!runDetail) return;
    setIsLoading(true);
    setErrorMessage(undefined);
    try {
      const detail = await cancelAgentRun(runDetail.id);
      setRunDetail(detail);
      setSelectedStepIndex(detail.steps[detail.steps.length - 1]?.step_index);
    } catch {
      setErrorMessage("실행을 취소하지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setDraft(INITIAL_DRAFT);
    setRunDetail(undefined);
    setSelectedStepIndex(undefined);
    setErrorMessage(undefined);
  };

  return {
    apiBaseUrl,
    draft,
    runDetail,
    selectedStep,
    isLoading,
    errorMessage,
    updateDraft,
    start,
    respond,
    cancel,
    selectStep: (step) => setSelectedStepIndex(step.step_index),
    refreshRun,
    reset,
  };
}

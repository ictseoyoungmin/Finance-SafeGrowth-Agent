import type { ReportResponse } from "../compliance/types";

export type AgentRunStatus = "running" | "awaiting_human" | "done" | "failed" | "cancelled";
export type AgentStepType = "thought" | "tool_call" | "tool_result" | "human_prompt" | "human_response" | "final";
export type AgentDecision = "approve" | "reject" | "revise" | "none";

export interface AgentRunRequest {
  content_id?: string;
  text?: string;
  user_message?: string;
  mode: "review" | "rewrite_only" | "explain";
  product_type?: string;
  channel?: string;
  target_customer?: string;
  language: string;
  initiator?: "user" | "scheduled";
}

export interface HumanPrompt {
  question: string;
  options?: string[] | null;
  proposed_action?: Record<string, unknown> | null;
}

export interface AgentStep {
  run_id: string;
  step_index: number;
  step_type: AgentStepType;
  tool_name?: string | null;
  payload: Record<string, unknown>;
  created_at?: string | null;
}

export interface AgentRunDetail {
  id: string;
  status: AgentRunStatus;
  started_at: string;
  ended_at?: string | null;
  content_id?: string | null;
  initiator?: string | null;
  user_message?: string | null;
  final_decision?: AgentDecision | null;
  final_summary?: string | null;
  token_input?: number | null;
  token_output?: number | null;
  model?: string | null;
  steps: AgentStep[];
  pending_human?: HumanPrompt | null;
  final_report?: ReportResponse | null;
}

import { getApiBaseUrl } from "../compliance/api";
import type { AgentRunDetail, AgentRunRequest } from "./types";

const API_BASE_URL = getApiBaseUrl();

export async function startAgentRun(request: AgentRunRequest): Promise<AgentRunDetail> {
  return postJson<AgentRunDetail>("/v1/agent/run", request);
}

export async function getAgentRun(runId: string): Promise<AgentRunDetail> {
  return getJson<AgentRunDetail>(`/v1/agent/runs/${runId}`);
}

export async function respondAgentRun(runId: string, response: unknown): Promise<AgentRunDetail> {
  return postJson<AgentRunDetail>(`/v1/agent/runs/${runId}/respond`, { response });
}

export async function cancelAgentRun(runId: string): Promise<AgentRunDetail> {
  return postJson<AgentRunDetail>(`/v1/agent/runs/${runId}/cancel`, {});
}

export function subscribeAgentStream(runId: string, onStep: () => void): EventSource | null {
  if (!("EventSource" in window)) {
    return null;
  }
  const source = new EventSource(`${API_BASE_URL}/v1/agent/runs/${runId}/stream`);
  source.addEventListener("step", onStep);
  source.addEventListener("status", onStep);
  source.onerror = () => source.close();
  return source;
}

async function postJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<TResponse>;
}

async function getJson<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return response.json() as Promise<TResponse>;
}

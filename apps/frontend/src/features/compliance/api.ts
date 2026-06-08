import type {
  AnalyzeRequest,
  AnalyzeResponse,
  ApprovalRequest,
  ApprovalResponse,
  EvidenceRequest,
  EvidenceResponse,
  FlaggedSpan,
  RecentContentsResponse,
  RegulationVersionDetail,
  ReportResponse,
  RewriteRequest,
  RewriteResponse,
} from "./types";

export const DEMO_TEXT =
  "[JB Bank] 신규 가입 특별 혜택! 누구나 가입 가능한 JB 글로벌 인컴 펀드로 연 5.0% 수익을 안정적으로 받아보세요. 원금 걱정 없이 시작하는 든든한 자산관리, 지금 신청하세요.";

export const DEFAULT_INPUT: AnalyzeRequest = {
  product_type: "투자상품",
  channel: "앱 푸시",
  target_customer: "30대 직장인",
  language: "ko",
  original_text: DEMO_TEXT,
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export async function analyzeContent(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  return postJson<AnalyzeResponse>("/v1/compliance/analyze", request);
}

export async function fetchEvidence(request: EvidenceRequest): Promise<EvidenceResponse> {
  return postJson<EvidenceResponse>("/v1/compliance/evidence", request);
}

export async function fetchRewrite(request: RewriteRequest): Promise<RewriteResponse> {
  return postJson<RewriteResponse>("/v1/compliance/rewrite", request);
}

export async function approveContent(request: ApprovalRequest): Promise<ApprovalResponse> {
  return postJson<ApprovalResponse>("/v1/compliance/approve", request);
}

export async function fetchReport(contentId: string): Promise<ReportResponse> {
  return getJson<ReportResponse>(`/v1/compliance/report?content_id=${encodeURIComponent(contentId)}`);
}

export async function fetchRecentContents(limit = 20): Promise<RecentContentsResponse> {
  return getJson<RecentContentsResponse>(`/v1/compliance/contents/recent?limit=${limit}`);
}

export async function fetchRegulationVersion(versionId: string): Promise<RegulationVersionDetail> {
  return getJson<RegulationVersionDetail>(
    `/v1/compliance/regulation-versions/${encodeURIComponent(versionId)}`,
  );
}

export async function deleteContent(contentId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/v1/compliance/contents/${encodeURIComponent(contentId)}`,
    { method: "DELETE" },
  );
  if (!response.ok && response.status !== 204) {
    throw new Error(`API request failed: ${response.status}`);
  }
}

export async function deleteAllContents(): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/v1/compliance/contents`, { method: "DELETE" });
  if (!response.ok && response.status !== 204) {
    throw new Error(`API request failed: ${response.status}`);
  }
}

export interface RecentAuditEntry {
  content_id: string;
  action: string;
  model_version?: string | null;
  created_at?: string | null;
}

export async function fetchRecentAuditEvents(limit = 10): Promise<{ entries: RecentAuditEntry[] }> {
  return getJson(`/v1/compliance/audit-log/recent?limit=${limit}`);
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

export class ApiNotAvailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiNotAvailableError";
  }
}

async function getJson<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (response.status === 404) {
    throw new ApiNotAvailableError(`해당 엔드포인트가 백엔드에 없습니다 (404): ${path}`);
  }
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<TResponse>;
}

export function fallbackAnalyze(request: AnalyzeRequest): AnalyzeResponse {
  const spans: FlaggedSpan[] = [
    buildSpan(request.original_text, "누구나", "과장 표현", "HIGH", "보편적 수혜 또는 조건 없는 혜택으로 오인될 수 있습니다.", 0.92),
    buildSpan(request.original_text, "연 5.0% 수익", "확정 수익 오인", "HIGH", "투자상품의 수익률을 확정적으로 받을 수 있는 것처럼 해석될 수 있습니다.", 0.95),
    buildSpan(request.original_text, "안정적으로", "안정성 오인", "MEDIUM", "투자 위험이나 변동 가능성이 낮은 것처럼 오인될 수 있습니다.", 0.87),
    buildSpan(request.original_text, "원금 걱정 없이", "원금 보장 오인", "HIGH", "원금 손실 가능성이 없는 것처럼 오인될 수 있습니다.", 0.96),
  ].filter((span) => span.start >= 0);

  return {
    content_id: "demo-content",
    risk_level: spans.some((span) => span.severity === "HIGH") ? "HIGH" : "LOW",
    flagged_spans: spans,
    risk_categories: Array.from(new Set(spans.map((span) => span.risk_category))),
    reviewer_notes:
      "투자상품 광고로 해석될 수 있으며 수익률, 안정성, 원금 관련 표현은 배포 전 완화가 필요합니다.",
  };
}

export function fallbackEvidence(contentId: string): EvidenceResponse {
  return {
    content_id: contentId,
    evidence_list: [
      {
        evidence_id: "doc-demo-001",
        title: "금융상품 광고 심사 가이드라인",
        version: "demo-v1",
        snippet: "투자성 상품 광고에서는 수익률을 확정적으로 표현하지 않아야 하며 손실 가능성을 함께 안내해야 합니다.",
        similarity: 0.87,
        version_id: "ver-demo-001",
        effective_date: "2026-01-15",
        risk_categories: ["확정 수익 오인", "안정성 오인"],
      },
      {
        evidence_id: "doc-demo-002",
        title: "금융소비자 보호 가이드라인",
        version: "demo-v1",
        snippet: "원금 손실 가능성이 있는 상품은 원금 보장 또는 원금 걱정이 없다는 취지로 안내하지 않아야 합니다.",
        similarity: 0.84,
        version_id: "ver-demo-002",
        effective_date: "2025-11-01",
        risk_categories: ["원금 보장 오인"],
      },
    ],
    guideline_snippets: ["수익률 확정 표현 금지", "원금 손실 가능성 고지 필요"],
  };
}

export function fallbackRewrite(contentId: string): RewriteResponse {
  return {
    content_id: contentId,
    revised_text_conservative:
      "본 상품은 시장 상황에 따라 수익 또는 손실이 발생할 수 있으며, 가입 전 상품설명서와 유의사항을 반드시 확인하시기 바랍니다.",
    revised_text_marketing:
      "시장 상황에 따라 수익은 변동될 수 있으며, 원금 손실 가능성이 있습니다. 가입 전 상품설명서와 유의사항을 확인해 주세요.",
    changes: [
      {
        original: "연 5.0% 수익을 안정적으로",
        replacement: "시장 상황에 따라 수익률은 변동될 수 있으며",
        reason: "확정 수익 및 안정성 오인 표현 완화",
      },
      {
        original: "원금 걱정 없이",
        replacement: "원금 손실 가능성이 있습니다",
        reason: "원금 보장 오인 표현을 필수 고지로 대체",
      },
    ],
    source: "fallback",
  };
}

function buildSpan(
  text: string,
  spanText: string,
  riskCategory: string,
  severity: "LOW" | "MEDIUM" | "HIGH",
  reason: string,
  confidence: number,
): FlaggedSpan {
  const start = text.indexOf(spanText);
  return {
    span_text: spanText,
    start,
    end: start >= 0 ? start + spanText.length : -1,
    risk_category: riskCategory,
    severity,
    reason,
    confidence,
  };
}

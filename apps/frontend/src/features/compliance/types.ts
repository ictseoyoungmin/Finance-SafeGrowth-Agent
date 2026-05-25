export type WorkflowStep = "input" | "redline" | "evidence" | "rewrite" | "approval";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH";

export interface AnalyzeRequest {
  product_type: string;
  channel: string;
  target_customer: string;
  language: string;
  original_text: string;
}

export interface FlaggedSpan {
  span_text: string;
  start: number;
  end: number;
  risk_category: string;
  severity: RiskLevel;
  reason: string;
  confidence: number;
  source?: "rule" | "gemini" | "llm";
}

export interface AnalyzeResponse {
  content_id: string;
  risk_level: RiskLevel;
  flagged_spans: FlaggedSpan[];
  risk_categories: string[];
  reviewer_notes: string;
}

export interface EvidenceRequest {
  content_id: string;
  risk_categories: string[];
  product_type: string;
}

export interface EvidenceItem {
  evidence_id: string;
  title: string;
  version: string;
  snippet: string;
  similarity: number;
  version_id?: string | null;
  effective_date?: string | null;
  risk_categories?: string[];
}

export interface RegulationVersionDetail {
  id: string;
  source_id: string;
  title: string;
  version_label?: string | null;
  effective_date?: string | null;
  content_hash: string;
  raw_text?: string | null;
  chunk_count: number;
  superseded_by?: string | null;
  ingested_at?: string | null;
}

export interface EvidenceResponse {
  content_id: string;
  evidence_list: EvidenceItem[];
  guideline_snippets: string[];
}

export interface RewriteRequest {
  content_id: string;
  mode: string;
}

export interface RewriteChange {
  original: string;
  replacement: string;
  reason: string;
}

export interface RewriteResponse {
  content_id: string;
  revised_text_conservative: string;
  revised_text_marketing: string;
  changes: RewriteChange[];
  source?: "gemini" | "fallback";
}

export type ApprovalDecision = "APPROVED" | "CONDITIONALLY_APPROVED" | "REJECTED" | "REVISION_REQUESTED";

export interface ApprovalRequest {
  content_id: string;
  reviewer: string;
  decision: ApprovalDecision;
  comment?: string;
  selected_revision?: string;
}

export interface ApprovalResponse {
  approval_id: string;
  content_id: string;
  status: string;
  decision: ApprovalDecision;
  reviewer: string;
}

export interface ReportResponse {
  content_id: string;
  summary: string;
  risk_level?: RiskLevel;
  final_text: string;
  evidence: Record<string, unknown>[];
  changes: Record<string, unknown>[];
  approval?: Record<string, unknown>;
  audit_log: Record<string, unknown>[];
}

export interface RecentContentItem {
  id: string;
  created_at?: string | null;
  product_type: string;
  channel: string;
  target_customer: string;
  language: string;
  original_text_preview: string;
  risk_level?: string | null;
  decision?: ApprovalDecision | string | null;
  reviewer?: string | null;
}

export interface RecentContentsResponse {
  items: RecentContentItem[];
}

export interface ComplianceState {
  step: WorkflowStep;
  input: AnalyzeRequest;
  analyze?: AnalyzeResponse;
  evidence?: EvidenceResponse;
  rewrite?: RewriteResponse;
  approval?: ApprovalResponse;
  report?: ReportResponse;
  selectedRevision: "conservative" | "marketing";
  usedFallback: boolean;
  isLoading: boolean;
  pendingAction?: "approve" | "reject" | "request_revision" | "load_report";
  errorMessage?: string;
  actionMessage?: string;
}

-- H4 · audit_logs metadata column for operational analytics
-- (e.g. {"rule_categories": ["과장 표현", "확정 수익 오인"]})
-- Safe to run repeatedly.

alter table if exists public.audit_logs
    add column if not exists metadata jsonb;

comment on column public.audit_logs.metadata is
    'Optional structured metadata (rule_categories, etc.) for metrics aggregation.';

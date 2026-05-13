-- JB SafeGrowth Agent PoC schema.
-- Demo regulation content is for MVP validation only and is not legal advice.

create extension if not exists vector;
create extension if not exists pgcrypto;

create table if not exists contents (
  id uuid primary key default gen_random_uuid(),
  product_type text not null,
  channel text not null,
  target_customer text not null,
  language text not null default 'ko',
  original_text text not null,
  created_at timestamptz not null default now()
);

create table if not exists risk_results (
  id uuid primary key default gen_random_uuid(),
  content_id uuid references contents(id) on delete cascade,
  risk_level text not null,
  flagged_spans jsonb not null default '[]'::jsonb,
  risk_categories text[] not null default '{}',
  reviewer_notes text,
  created_at timestamptz not null default now()
);

create table if not exists regulation_docs (
  id text primary key,
  title text not null,
  version text not null,
  product_type text not null default '공통',
  risk_categories text[] not null default '{}',
  body text not null,
  snippet text not null,
  guideline_snippet text not null,
  embedding vector(768),
  created_at timestamptz not null default now()
);

create index if not exists regulation_docs_product_type_idx
  on regulation_docs(product_type);

create index if not exists regulation_docs_risk_categories_idx
  on regulation_docs using gin(risk_categories);

create index if not exists regulation_docs_embedding_idx
  on regulation_docs using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

create table if not exists approval_logs (
  id uuid primary key default gen_random_uuid(),
  content_id uuid references contents(id) on delete set null,
  reviewer text not null,
  decision text not null,
  comment text,
  created_at timestamptz not null default now()
);

create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  content_id uuid references contents(id) on delete set null,
  action text not null,
  model_version text not null,
  doc_version text not null,
  prompt_hash text,
  created_at timestamptz not null default now()
);

create or replace function match_regulation_docs(
  query_embedding vector(768),
  match_product_type text,
  match_risk_categories text[],
  match_count int default 5
)
returns table (
  evidence_id text,
  title text,
  version text,
  snippet text,
  guideline_snippet text,
  similarity float
)
language sql
stable
as $$
  select
    id as evidence_id,
    title,
    version,
    snippet,
    guideline_snippet,
    1 - (embedding <=> query_embedding) as similarity
  from regulation_docs
  where embedding is not null
    and product_type in (match_product_type, '공통')
    and (
      coalesce(array_length(match_risk_categories, 1), 0) = 0
      or risk_categories && match_risk_categories
    )
  order by embedding <=> query_embedding
  limit match_count;
$$;

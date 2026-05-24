-- SafeGrowth Agent PoC schema.
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

create table if not exists regulation_sources (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  source_type text not null check (source_type in ('admin_upload','rss','manual_seed')),
  url text,
  product_type text,
  default_risk_categories text[] not null default '{}',
  last_polled_at timestamptz,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists regulation_versions (
  id uuid primary key default gen_random_uuid(),
  source_id uuid references regulation_sources(id) on delete cascade,
  title text not null,
  version_label text,
  effective_date date,
  content_hash text not null,
  raw_text text,
  chunk_count int not null default 0,
  superseded_by uuid references regulation_versions(id),
  ingested_at timestamptz not null default now(),
  unique (source_id, content_hash)
);

create table if not exists regulation_chunks (
  id bigserial primary key,
  version_id uuid not null references regulation_versions(id) on delete cascade,
  chunk_index int not null,
  chunk_text text not null,
  risk_categories text[] not null default '{}',
  product_type text,
  embedding vector(768),
  created_at timestamptz not null default now(),
  unique (version_id, chunk_index)
);

create index if not exists regulation_sources_active_idx
  on regulation_sources(active);

create index if not exists regulation_versions_source_ingested_idx
  on regulation_versions(source_id, ingested_at desc);

create index if not exists regulation_versions_hash_idx
  on regulation_versions(source_id, content_hash);

create index if not exists regulation_chunks_product_type_idx
  on regulation_chunks(product_type);

create index if not exists regulation_chunks_risk_categories_idx
  on regulation_chunks using gin(risk_categories);

create table if not exists approval_logs (
  id uuid primary key default gen_random_uuid(),
  content_id uuid references contents(id) on delete set null,
  reviewer text not null,
  decision text not null,
  comment text,
  selected_revision text,
  created_at timestamptz not null default now()
);

alter table approval_logs
  add column if not exists selected_revision text;

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

grant usage on schema public to anon, authenticated, service_role;

grant select, insert, update, delete on table public.contents to service_role;
grant select, insert, update, delete on table public.risk_results to service_role;
grant select, insert, update, delete on table public.audit_logs to service_role;
grant select, insert, update, delete on table public.approval_logs to service_role;
grant select, insert, update, delete on table public.regulation_docs to service_role;
grant select, insert, update, delete on table public.regulation_sources to service_role;
grant select, insert, update, delete on table public.regulation_versions to service_role;
grant select, insert, update, delete on table public.regulation_chunks to service_role;
grant usage, select on sequence public.regulation_chunks_id_seq to service_role;

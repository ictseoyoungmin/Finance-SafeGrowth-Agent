create extension if not exists vector;
create extension if not exists pgcrypto;

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

grant usage on schema public to anon, authenticated, service_role;
grant select, insert, update, delete on table public.regulation_sources to service_role;
grant select, insert, update, delete on table public.regulation_versions to service_role;
grant select, insert, update, delete on table public.regulation_chunks to service_role;
grant usage, select on sequence public.regulation_chunks_id_seq to service_role;

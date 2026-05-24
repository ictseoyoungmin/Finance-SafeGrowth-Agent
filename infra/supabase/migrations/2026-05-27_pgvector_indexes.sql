create extension if not exists vector;

create index if not exists regulation_chunks_embedding_idx
  on regulation_chunks using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

create or replace function match_regulation_chunks(
  query_embedding vector(3072),
  match_count int default 5,
  match_product_type text default '공통',
  match_risk_categories text[] default '{}'
)
returns table (
  id bigint,
  version_id uuid,
  chunk_text text,
  risk_categories text[],
  product_type text,
  similarity float
)
language sql
stable
as $$
  select
    c.id,
    c.version_id,
    c.chunk_text,
    c.risk_categories,
    c.product_type,
    1 - (c.embedding <=> query_embedding) as similarity
  from regulation_chunks c
  join regulation_versions v on v.id = c.version_id
  where c.embedding is not null
    and v.superseded_by is null
    and c.product_type in (match_product_type, '공통')
    and (
      coalesce(array_length(match_risk_categories, 1), 0) = 0
      or c.risk_categories && match_risk_categories
    )
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

grant execute on function match_regulation_chunks(vector, int, text, text[]) to service_role;

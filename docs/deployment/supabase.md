# Supabase Setup

Supabase stores future persistent content, risk results, regulation documents, approval logs, and audit logs.

## Required Extensions

`infra/supabase/schema.sql` enables:

- `vector`
- `pgcrypto`

## Apply Schema And Seeds

Run these SQL files in Supabase SQL Editor or through the Supabase CLI in this order:

```text
infra/supabase/schema.sql
infra/supabase/seed_regulation_docs.sql
infra/supabase/seed_demo_contents.sql
```

## Verification Queries

```sql
select count(*) from regulation_docs;
select title, version, product_type from regulation_docs order by id;
```

The RPC requires a real embedding for production vector search. The MVP backend currently returns deterministic fallback evidence when Supabase is unavailable.

## Seed Caveat

The seed regulation documents are PoC sample guidance for demo validation only. They are not legal advice and should be replaced with reviewed internal policy content before production use.

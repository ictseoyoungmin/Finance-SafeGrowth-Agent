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

In the SQL Editor, paste the SQL file contents. Do not paste the file path itself. Running a path such as `infra/supabase/schema.sql` in the SQL Editor will fail with a syntax error near `infra`.

Current production setup status, 2026-05-20:

- Live Supabase verification status: VERIFIED.
- Supabase project created at `https://eszuojttibhkazrtqrqx.supabase.co`.
- `infra/supabase/schema.sql` was applied successfully through the SQL Editor.
- `infra/supabase/seed_regulation_docs.sql` was applied successfully through the SQL Editor.
- Render stores the Supabase environment variables.
- Vercel does not store Supabase secrets. Vercel only needs `VITE_API_BASE_URL=https://finance-safegrowth-agent.onrender.com`.

## Runtime Environment

Backend-only variables:

```dotenv
SUPABASE_URL=https://eszuojttibhkazrtqrqx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...
```

`SUPABASE_URL` must be the project base URL. Do not include `/rest/v1/`; the backend appends `/rest/v1/{table}` internally.

The project uses the newer Supabase API key style:

- publishable key -> `SUPABASE_ANON_KEY`
- secret key -> `SUPABASE_SERVICE_ROLE_KEY`

Never commit the secret key and never expose it to Vercel or frontend code.

## Data API Grants

The production project was created with strict security settings:

- Data API enabled
- Automatically expose new tables disabled
- Automatic RLS enabled

Because of that, the first Render insert to `POST /rest/v1/contents` returned `403 Forbidden`. The operational fix was to grant the service role access to the public tables from the Supabase SQL Editor:

```sql
grant usage on schema public to anon, authenticated, service_role;

grant select, insert, update, delete on table public.contents to service_role;
grant select, insert, update, delete on table public.risk_results to service_role;
grant select, insert, update, delete on table public.audit_logs to service_role;
grant select, insert, update, delete on table public.approval_logs to service_role;
grant select, insert, update, delete on table public.regulation_docs to service_role;
```

After applying grants, re-test live persistence through the public Render `/v1/compliance/analyze` endpoint and confirm rows in the Supabase Table Editor:

- `contents` has a new row.
- `risk_results` has a new row.
- `audit_logs` has a new row with `action = analyze`.

## Day 10 Schema Update

Day 10 adds approval persistence. Existing Supabase projects should re-run the updated `infra/supabase/schema.sql` or apply the equivalent migration:

```sql
alter table approval_logs
  add column if not exists selected_revision text;
```

Without this column, live `POST /v1/compliance/approve` may fall back to in-memory storage when it attempts to store the selected revision.

After the Day 11 follow-up frontend fix is deployed, verify the latest UI approval row:

- `approval_logs.selected_revision` contains the actual approved sentence.
- `approval_logs.selected_revision` is not `marketing`.
- `approval_logs.selected_revision` is not `conservative`.

## Verification Queries

```sql
select count(*) from regulation_docs;
select title, version, product_type from regulation_docs order by id;
```

The RPC requires a real embedding for production vector search. The MVP backend currently returns deterministic fallback evidence when Supabase is unavailable.

## Seed Caveat

The seed regulation documents are PoC sample guidance for demo validation only. They are not legal advice and should be replaced with reviewed internal policy content before production use.

## Delete Policy (R-C-2)

`DELETE /v1/compliance/contents/{id}` and the bulk `DELETE /v1/compliance/contents`
only remove the parent row from `contents`. The schema defines:

| child table | on delete |
| --- | --- |
| `risk_results` | **CASCADE** — automatically removed |
| `approval_logs` | **SET NULL** — row preserved with `content_id = NULL` |
| `audit_logs` | **SET NULL** — row preserved with `content_id = NULL` |

The approval / audit trail therefore survives content deletion by design, so
the backend does not issue bulk deletes against those tables. In fallback
in-memory mode, only the `risk_results` cache is pruned along with the
content; approval / audit fallback maps are kept for parity with Supabase.

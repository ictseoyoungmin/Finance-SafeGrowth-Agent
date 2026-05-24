-- Week 3 Day 15: agent_runs / agent_steps tables for AI Agent loop.
-- Apply through Supabase SQL Editor (paste contents, do not paste the file path).

create extension if not exists pgcrypto;

create table if not exists agent_runs (
  id uuid primary key default gen_random_uuid(),
  content_id uuid references contents(id) on delete set null,
  status text not null
    check (status in ('running','awaiting_human','done','failed','cancelled')),
  initiator text,
  user_message text,
  final_decision text,
  final_summary text,
  final_report jsonb,
  started_at timestamptz not null default now(),
  ended_at timestamptz,
  token_input int,
  token_output int,
  model text
);

create index if not exists agent_runs_content_id_idx on agent_runs(content_id);
create index if not exists agent_runs_status_idx on agent_runs(status);
create index if not exists agent_runs_started_at_idx on agent_runs(started_at desc);

create table if not exists agent_steps (
  id bigserial primary key,
  run_id uuid not null references agent_runs(id) on delete cascade,
  step_index int not null,
  step_type text not null
    check (step_type in ('thought','tool_call','tool_result','human_prompt','human_response','final')),
  tool_name text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create unique index if not exists agent_steps_run_step_idx on agent_steps(run_id, step_index);
create index if not exists agent_steps_run_id_idx on agent_steps(run_id);

grant usage on schema public to anon, authenticated, service_role;

grant select, insert, update, delete on table public.agent_runs to service_role;
grant select, insert, update, delete on table public.agent_steps to service_role;
grant usage, select on sequence public.agent_steps_id_seq to service_role;

# Week 3 — Agent Conversion Workplan

Week 3는 Week 1/2에서 만든 "5-step 워크플로 + LLM 단발 호출 2회" 구현물을 **JB Fin:AI Challenge 명세에 맞는 진짜 AI Agent**로 전환하는 작업이다.

대회 명세의 핵심 명제:

> "AI가 상황과 데이터를 이해하고 필요한 정보를 바탕으로 판단하며, 적절한 행동이나 지원을 수행하는 **Agent형 서비스** 개발을 지향합니다."
>
> 지정주제 2 Compliance AI: "**AI 규제 Agent**가 최신 금융규제와 내부 기준을 자동으로 추적합니다."

현재 제출 위험 — 자세한 진단은 `00-architecture-and-agent-design.md` "Why this is not yet an Agent" 절 참조.

## Week 3 3대 전환 축

1. **Agent loop 도입.** LLM function-calling 기반 자체 ReAct 루프. Agent가 어떤 도구를 어떤 순서로 호출할지 스스로 결정한다.
2. **LLM provider 전환.** Gemini와 shared local OpenAI-compatible LLM server를 환경변수만으로 스위칭한다.
3. **실제 규제 추적.** 외부 규제 소스 ingestion 파이프라인 + 스케줄러 + 버전 관리로 "최신 규제 자동 추적"을 실제로 구현한다.
4. **Agent trace UI.** 5-step wizard를 agent 실행 trace 뷰로 재구성. 사람은 단계 진행이 아니라 agent 판단 검토·승인만 한다.

## 작업 원칙

- P0 슬라이스(agent loop + tools + trace UI)를 먼저 완료한다. 이게 안 되면 "Agent" 명제가 깨진다.
- LLM provider 미설정/오프라인 상황에서도 deterministic fallback agent run이 동작해야 한다 (rule-only tool chain).
- Supabase 미설정 시 in-memory trace store로 fallback.
- 기존 5-step API (`/v1/compliance/analyze`, `/evidence`, `/rewrite`, `/approve`, `/report`)는 **호환성을 위해 유지**한다. Agent runner는 이 endpoint들을 tool로 감싸서 사용한다.
- 각 day 종료 시 해당 문서의 Completion Log를 갱신한다.

## 일별 슬라이스

| Day | 문서 | 우선순위 | 목표 |
|---|---|---|---|
| Day 15 | `day-15-agent-contracts-and-state.md` | P0 | Tool 계약, Agent 상태/trace 스키마, Supabase 마이그레이션 |
| Day 16 | `day-16-tool-extraction.md` | P0 | 기존 service들을 tool 함수로 추출, registry 구성 |
| Day 17 | `day-17-agent-runner.md` | P0 | Gemini function-calling loop, `/v1/agent/run` endpoint, fallback agent |
| Day 18 | `day-18-llm-provider-abstraction.md` | P0 | Gemini/local OpenAI-compatible LLM provider abstraction, Docker local LLM switching |
| Day 19 | `day-19-regulation-ingestion.md` | P1 | 외부 규제 소스 connector, ingestion CLI, `regulation_versions` 테이블 |
| Day 20 | `day-20-vector-rag.md` | P1 | 실제 embedding (Gemini text-embedding), pgvector 검색 |
| Day 21 | `day-21-frontend-agent-trace.md` | P0 | Agent run / trace 화면, 기존 wizard는 legacy 모드로 유지 |
| Day 22 | `day-22-evaluation-and-handover.md` | P2 | 평가 시나리오, 심사 기준 fit 문서, demo freeze |

우선순위 매핑:

- **P0 (Day 15, 16, 17, 18, 21)**: "Agent가 아니다" 결함을 해소하고 로컬 LLM 시연 경로를 확보하는 최소 셋.
- **P1 (Day 19, 20)**: "최신 규제 자동 추적" 명제와 RAG 신뢰도를 회복한다. P0 후 즉시 진행.
- **P2 (Day 22)**: demo 안정화·심사 대응 문서.

## 표준 시나리오 (Agent run input)

Week 1/2 표준 데모 문장을 그대로 사용한다.

```text
지금 가입하면 누구나 연 8% 수익을 안정적으로 받을 수 있는 JB 투자상품! 원금 걱정 없이 시작하세요.
```

기대 agent 행동(예시 trace):

```text
1. scan_rules(text)               -> 4건 risky span 탐지, HIGH
2. search_regulation(categories)  -> 3건 evidence 회수
3. draft_rewrite(...)             -> conservative/marketing 2안
4. request_human_review(...)      -> 사용자 승인 대기
5. finalize_report(...)           -> approval 후 최종 리포트
```

Agent는 자유 입력(예: "원금 보장 표현 없음, 위험 고지 충분")에 대해서는 step 2~3을 건너뛸 수도 있어야 한다.

## 공통 완료 기준

- Backend: `ruff check app tests`, `pytest` (agent runner / tool registry / regulation ingestion 단위 테스트 포함)
- Frontend: `npm run lint`, `npm run typecheck`, `npm run build`, agent run 화면 Playwright smoke
- 수동 flow: 입력 → agent run → trace 검토 → 사람 승인 → 최종 리포트
- LLM provider 또는 Supabase 미설정 상황에서도 deterministic fallback agent run이 끝까지 동작

## Phase 매핑

Week 3는 phase3 슬라이스를 별도로 만들지 않는다. day-XX 문서 자체가 슬라이스 단위다. Phase2 README의 "review baseline / p0 / p1 / p2" 분류 규칙은 그대로 따른다(위 표의 우선순위 칸 참조).

## 구현 완료 기록

- [x] Day 15 완료 (2026-05-24)
- [x] Day 16 완료 (2026-05-24)
- [x] Day 17 완료 (2026-05-24)
- [x] Day 18 완료 (2026-05-24)
- [ ] Day 19 완료
- [ ] Day 20 완료
- [ ] Day 21 완료
- [ ] Day 22 완료

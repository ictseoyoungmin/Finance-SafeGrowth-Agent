# R-E-2 · Frontend LoginPage + AuthContext + reviewer profile

R-E-1 의 backend 위에 진입점 로그인 UI 와 사용자 정보 반영.

## 흐름

```
app start
  → AuthContext 가 localStorage 에서 token 복원
  → 유효? me() 호출로 profile 검증
      pass → 기존 라우팅 그대로
      fail → LoginPage
  → 미인증 → LoginPage
```

## LoginPage
- id / password 텍스트 필드
- id 와 password 모두 default value = `tester` (prefill)
- "로그인" 버튼 → `/v1/auth/login`
- 실패 시 inline 오류 메시지 ("로그인 정보가 올바르지 않습니다.")
- 성공 시 token 저장 + AuthContext 갱신 + 메인으로 이동

## AuthContext
- profile, token, login(), logout()
- api wrapper (existing `fetch` 호출들) 가 token 있으면 `Authorization: Bearer` 첨부.
  최소 변경 위해 `api.ts` 의 `postJson` / `getJson` 에 헤더 주입 로직 한 군데 추가.

## Profile 반영 위치 (현재 fixture 박힌 곳들)
| 위치 | 현재 | 변경 |
| --- | --- | --- |
| 헤더 우상단 팀 배지 | "관리자 준법감시팀" hardcode | `profile.team` |
| 헤더 우상단 이름/직책 | "김준법 수석 / Compliance Manager" hardcode | `profile.display_name` / `profile.title` |
| 승인 요청 reviewer (`approveContent`) | "Compliance Reviewer" hardcode | `profile.display_name` |
| 리포트 패키지 검토자 (`ReportPackagePanel`) | `approval.reviewer ?? "기록 없음"` — backend 가 reviewer 저장 | 변경 없음 (승인 시 profile 이미 들어감) |

`approveContent` 요청에 reviewer 를 profile.display_name 으로 전달하도록 store 수정.

## DELETE UI gating
- HistoryPage 의 삭제 버튼 → `profile.role === "admin"` 일 때만 노출
- tester 는 버튼 자체 안 보임
- 호출 시 token 자동 첨부 (api wrapper)

## Logout
- 헤더 우상단에 작은 "로그아웃" 버튼/메뉴
- 로그아웃 시 token 삭제 + LoginPage 로

## 테스트 (수동)
- 로그인 X → 어떤 페이지도 못 봄
- tester 로그인 → 분석 흐름 OK, 삭제 버튼 안 보임
- admin 로그인 → 삭제 버튼 보임 + 동작
- 헤더에 본인 이름/팀 표시
- 리포트 검토자 = 본인 이름

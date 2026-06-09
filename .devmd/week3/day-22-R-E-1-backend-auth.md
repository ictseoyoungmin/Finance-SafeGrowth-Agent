# R-E-1 · Backend auth + role-protected DELETE + supabase delete fix

피드백 #1 (DELETE 인증 누락) + #2 (Supabase delete false-negative) 통합.

## 결정

### 사전 계정 (회원가입 없음)
| role | id | password 출처 | profile (display_name / title / team) |
| --- | --- | --- | --- |
| tester | `tester` | hardcode `tester` (frontend prefill) | "테스트 검토자 / Tester / 테스트 팀" |
| admin | `admin` (또는 settings.admin_id) | env `ADMIN_PASSWORD` (필수) | "김준법 수석 / Compliance Manager / 준법감시팀" |

`ADMIN_PASSWORD` 미설정 시 backend 가 admin 로그인은 거절, tester 만 통과. dev 편의용 `.env.example` 에 placeholder.

### 인증 방식
- 로그인 → opaque UUID 토큰 발급 + in-memory map `{token: profile}`
- 보호된 요청 → `Authorization: Bearer <token>` 헤더
- 토큰 발급 시 expires_at = now + N hours (default 8h). 만료 시 401.

### 권한
- **tester**: 읽기/분석/수정안 생성/승인 — 기존 흐름 전체 사용 가능
- **admin**: tester + DELETE
- DELETE `/contents/{id}`, DELETE `/contents` 에 `require_admin_role` 적용
- 기존 `x-admin-token` (legacy, regulation ingest) 도 그대로 인정 — 통합 비용 절감

## 모듈 구조

```
app/core/auth.py            # require_admin_role, require_authenticated, AuthProfile
app/services/auth_service.py  # login, logout, lookup
app/schemas/auth.py         # LoginRequest, LoginResponse, AuthProfile
app/api/v1/auth.py          # /v1/auth/login, /v1/auth/logout, /v1/auth/me
```

기존 `app.api.v1.admin.require_admin_token` 은 유지하되 `app.core.auth` 의
`require_admin_role` 가 둘 다 (Bearer + x-admin-token) 인정.

## /v1/auth API

```
POST /v1/auth/login          { id, password } -> { token, profile }
POST /v1/auth/logout         (Bearer) -> 204
GET  /v1/auth/me             (Bearer) -> profile
```

## ContentRepository.delete() 버그 (피드백 #2)

현재:
```python
def delete(self, content_id: str) -> bool:
    if self._supabase_client.is_configured:
        try:
            self._supabase_client.delete("contents", {"id": content_id})
        except Exception: ...
    return FALLBACK_CONTENTS.pop(content_id, None) is not None
```

Supabase 모드에서 실제 row 가 삭제됐어도 fallback 에 entry 없으면 False
반환 → `delete_content` 라우터가 404 던짐.

수정:
```python
def delete(self, content_id: str) -> bool:
    if self._supabase_client.is_configured:
        try:
            deleted = self._supabase_client.delete("contents", {"id": content_id})
            # Supabase REST 의 delete 가 row 반환하면 그걸 truthy 로 사용,
            # 아니면 성공 가정. fallback pop 결과는 OR.
            return bool(deleted) or FALLBACK_CONTENTS.pop(content_id, None) is not None
        except Exception:
            logger.exception("Supabase contents delete failed; falling back to memory store.")
    return FALLBACK_CONTENTS.pop(content_id, None) is not None
```

`SupabaseClient.delete` 의 실제 반환 시그니처를 먼저 확인하고 맞춰 조정.

## 테스트
- auth_service login/logout/lookup
- `require_admin_role` 에 Bearer 없으면 401, tester 토큰이면 403, admin 토큰이면 통과
- `require_admin_role` 가 legacy x-admin-token 도 인정
- ContentRepository.delete Supabase mock 성공 시 True

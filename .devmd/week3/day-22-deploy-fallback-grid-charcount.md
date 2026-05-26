# Day 22 — DB fallback · Fallback 사유 · 승인 액션 grid · 카운터 anchor

## 배경

Render production 배포 후에도 5건의 후속 이슈:

1. **DB 인스턴스 여전히 404**: 백엔드 라우트는 배포되었으나, production 은 Supabase 가 configured 라서 `get(version_id)` 가 Supabase 조회 결과(None) 만 보고 404 반환. evidence 는 fallback 경로에서 `ver-demo-001/002/003` 으로 만들어졌는데 그 ID 가 실제 Supabase 에는 없음 → 조회 실패.
2. **fallback 사유 불투명**: RewriteStep 의 "기본 패턴 기반 (fallback)" chip 만 보여서, *왜* fallback 으로 떨어졌는지 (LLM 실패? 형식 오류?) 알 수 없음.
3. **ApprovalStep 액션 6개가 1줄 wrap**: 조건부 승인 / 반려 / 수정 요청 / 리포트 패키지 보기 / 수정안으로 / 처음으로 가 한 줄에 모두 들어가다 wrap 됨. 의미 단위 (결정 3 / 후속 3) 가 시각적으로 안 묶임.
4. **카운터 chip 여전히 미세 우측 overflow**: absolute right:0 으로 정렬했는데도 사용자 화면에서 textarea 우측 경계 밖으로 살짝 나옴. label 자체의 폭과 textarea 폭이 sub-pixel 단위로 어긋나는 듯.
5. **백엔드 재배포 트리거**: 사용자 명시 요청. Render 는 main push 시 자동 deploy.

## 목표

- production 에서도 `ver-demo-*` 같은 fallback ID 가 DB 인스턴스 모달에서 정상 표시되도록 — Supabase 결과가 비어도 fallback dict 로 떨어짐
- fallback chip 옆에 `?` HelpHint: "Gemini API 호출이 실패했거나 응답이 기대 형식과 달라, 입력 문장 기반 결정형 규칙으로 수정안을 생성했습니다." 같은 설명
- ApprovalStep 액션을 명시적 3x2 grid (결정 행 / 후속 행) 로
- 카운터 chip 을 **textarea 내부** 우상단으로 absolute 오버레이 → textarea 박스와 절대로 align 어긋날 수 없음
- main 에 commit + push → Render 자동 deploy

## 변경 사항

### 1. 백엔드 — get() 에 fallback chain

`apps/backend/app/repositories/regulation_versions_repo.py`

```python
def get(self, version_id: str) -> RegulationVersion | None:
    if self._supabase_client.is_configured:
        try:
            row = self._supabase_client.select_one("regulation_versions", {"id": version_id})
            if row:
                return RegulationVersion.model_validate(row)
        except Exception:
            logger.exception("Supabase regulation version get failed; falling back to demo seed.")
    row = FALLBACK_REGULATION_VERSIONS.get(version_id)
    return RegulationVersion.model_validate(row) if row else None
```

차이:
- Supabase 가 configured 라도 row 가 None 이면 fallback dict 도 본다
- 기존: configured 면 fallback 안 봄 → demo ID 들이 항상 404

테스트 케이스:
- Supabase configured + Supabase 에 해당 row 있음 → Supabase row 반환
- Supabase configured + Supabase 에 없음 + fallback 에 있음 → fallback 반환 (demo 데이터 응답)
- Supabase configured + 둘 다 없음 → None (404)
- Supabase not configured → fallback 만 본다 (기존 동작)

### 2. RewriteStep fallback 사유 hint

`apps/frontend/src/features/compliance/steps/RewriteStep.tsx`
- `sourceLabel` chip 옆에 `<HelpHint hint="..." />` 추가 (fallback 일 때만)
- hint:
  > "Gemini API 호출이 실패했거나 응답 형식이 예상과 달라, 입력 문장 기반 결정형 규칙(rule-based)으로 수정안을 생성했습니다. 결과는 안전한 표현 완화 중심이며, 실제 LLM 결과 대비 다양성이 낮을 수 있습니다."

### 3. ApprovalStep 액션 grid

`apps/frontend/src/features/compliance/steps/ApprovalStep.tsx`
- 기존 `<div className="action-row">` flex-wrap → 새 `<div className="approval-actions">` (CSS grid 2 rows × 3 cols)
- 행 의미:
  - row 1: 결정 (조건부 승인 / 반려 / 수정 요청)
  - row 2: 후속 (리포트 패키지 보기 / 수정안으로 / 처음으로)
- 좁은 폭에서는 1-column 으로 떨어짐 (모바일)

CSS:
```css
.approval-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 8px;
}
.approval-actions button { width: 100%; }
@media (max-width: 720px) {
  .approval-actions { grid-template-columns: 1fr; }
}
```

### 4. 카운터 textarea wrapper anchor

`apps/frontend/src/features/compliance/steps/InputStep.tsx`
- textarea 와 character-count 를 `<div className="textarea-wrap">` 로 감싼다
- chip 은 wrap 의 absolute top-right (textarea padding 안쪽)

```tsx
<label className="copy-field">
  <span className="copy-field__label">콘텐츠 입력 <HelpHint hint={HINTS.text} /></span>
  <div className="textarea-wrap">
    <textarea ... />
    <small className="character-count character-count--inside">
      <strong>{characterCount.toLocaleString()}</strong> / 2,000
    </small>
  </div>
</label>
```

CSS:
```css
.textarea-wrap {
  position: relative;
}
.character-count--inside {
  position: absolute;
  bottom: 10px;
  right: 14px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(2px);
  pointer-events: none;
}
```

textarea 의 우측 padding(16px) 보다 살짝 안쪽 (14px) 에 배치 — textarea 박스 안쪽이라 절대 밖으로 안 나감. backdrop blur 로 텍스트와 겹쳐도 가독성 유지. `pointer-events: none` 으로 textarea 클릭 방해 안 함.

기존 `.character-count--floating` 클래스와 분리 (다른 step 에서 쓸 수 있음).

### 5. 배포

- 모든 변경 commit
- `git push origin main` → Render 가 webhook 으로 자동 build & deploy

commit message: `Day 22 — DB lookup fallback · evidence hint · approval grid · char-count anchor`

## 영향 범위

| 영역 | 파일 |
| --- | --- |
| 백엔드 | `repositories/regulation_versions_repo.py` |
| 프론트 | `steps/RewriteStep.tsx`, `steps/ApprovalStep.tsx`, `steps/InputStep.tsx`, `styles.css` |

## 검증

- frontend `npm run build`, backend `pytest -q`
- 캡처:
  - 카운터 textarea 내부 우상단에 깔끔 정렬
  - RewriteStep chip 옆 `?` hover 풍선
  - ApprovalStep 3x2 grid (3개씩 두 줄)
  - DB 인스턴스 모달: production deploy 후 ver-demo-001 정상 응답

## 롤백

각 hunk 별. 백엔드 `get()` 변경은 add-only (기존 분기 결과를 약화시키지 않음) 라 안전.

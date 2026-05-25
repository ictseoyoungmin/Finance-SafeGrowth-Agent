import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

export function InputStep({ workflow }: StepProps) {
  const { state, updateInput, startReview } = workflow;
  const characterCount = state.input.original_text.length;

  return (
    <div className="input-screen">
      <header className="panel-heading">
        <h2>콘텐츠 입력</h2>
        <p>검토할 마케팅 콘텐츠의 정보를 입력해주세요.</p>
      </header>

      <div className="input-grid">
        <label>
          <span>상품 유형 <small>?</small></span>
          <select
            value={state.input.product_type}
            onChange={(event) => updateInput({ product_type: event.target.value })}
          >
            <option>투자상품</option>
            <option>예금상품</option>
            <option>대출상품</option>
            <option>카드상품</option>
          </select>
        </label>
        <label>
          <span>채널 <small>?</small></span>
          <select
            value={state.input.channel}
            onChange={(event) => updateInput({ channel: event.target.value })}
          >
            <option>앱 푸시</option>
            <option>문자 메시지</option>
            <option>웹 배너</option>
            <option>이메일</option>
          </select>
        </label>
        <label>
          <span>타겟 고객 <small>?</small></span>
          <select
            value={state.input.target_customer}
            onChange={(event) => updateInput({ target_customer: event.target.value })}
          >
            <option>30대 직장인</option>
            <option>신규 고객</option>
            <option>일반 투자자</option>
            <option>기존 고객</option>
          </select>
        </label>
        <label>
          <span>언어 <small>?</small></span>
          <select
            value={state.input.language}
            onChange={(event) => updateInput({ language: event.target.value })}
          >
            <option value="ko">한국어</option>
            <option value="en">English</option>
          </select>
        </label>
      </div>

      <label className="copy-field">
        <span>
          콘텐츠 입력 <small>?</small>
        </span>
        <textarea
          rows={8}
          value={state.input.original_text}
          onChange={(event) => updateInput({ original_text: event.target.value })}
        />
        <small className="character-count">{characterCount.toLocaleString()} / 2,000</small>
      </label>

      <div className="analysis-note">준법 리스크를 분석하고, 근거와 함께 수정안을 생성합니다.</div>

      <div className="input-readiness">
        <span>검토 준비</span>
        <strong>규정 기반 리스크 분석 · 근거 매칭 · 수정안 생성</strong>
        <small>입력한 정보는 분석 문맥으로 사용되며, 승인 패키지까지 연결됩니다.</small>
      </div>

      <div className="action-row centered">
        <button
          className="primary-button"
          onClick={startReview}
          disabled={state.isLoading}
          aria-busy={state.isLoading}
        >
          {state.isLoading ? "검토 중..." : "준법검토 시작"}
        </button>
      </div>
    </div>
  );
}

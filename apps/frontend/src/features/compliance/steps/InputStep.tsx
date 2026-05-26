import { HelpHint } from "../../../components/HelpHint";
import type { ComplianceWorkflow } from "../store";

interface StepProps {
  workflow: ComplianceWorkflow;
}

const HINTS = {
  product:
    "검토할 콘텐츠가 광고하는 금융상품 종류입니다. 규정 매칭과 리스크 분석의 1차 기준이 됩니다.",
  channel:
    "콘텐츠가 노출되는 매체입니다. 채널별 표현 규정과 글자수 제약이 다릅니다.",
  target:
    "주요 광고 대상 고객층입니다. 위험 표현 허용도와 필수 고지 사항이 달라집니다.",
  language: "콘텐츠 작성 언어입니다. 분석 모델과 규정 DB 선택에 사용됩니다.",
  text:
    "검토할 마케팅 문안을 그대로 붙여넣으세요. 2,000자까지 분석합니다. 입력 내용은 진행 중인 검토에 한해 브라우저에 임시 저장됩니다.",
};

export function InputStep({ workflow }: StepProps) {
  const { state, updateInput, startReview, goTo } = workflow;
  const characterCount = state.input.original_text.length;
  const hasPriorReview = Boolean(state.analyze);

  return (
    <div className="input-screen">
      <header className="panel-heading">
        <h2>콘텐츠 입력</h2>
        <p>검토할 마케팅 콘텐츠의 정보를 입력해주세요.</p>
      </header>

      {hasPriorReview ? (
        <div className="resume-banner" role="status">
          <div>
            <strong>이전 검토 결과가 있습니다</strong>
            <small>
              위험도 {state.analyze?.risk_level} · 탐지 {state.analyze?.flagged_spans.length}건. 입력
              값을 바꾸지 않으면 같은 결과를 다시 볼 수 있습니다.
            </small>
          </div>
          <button
            type="button"
            className="secondary-button"
            onClick={() => goTo("redline")}
          >
            검토 결과 보기 →
          </button>
        </div>
      ) : null}

      <div className="input-grid">
        <label>
          <span>
            상품 유형 <HelpHint hint={HINTS.product} />
          </span>
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
          <span>
            채널 <HelpHint hint={HINTS.channel} />
          </span>
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
          <span>
            타겟 고객 <HelpHint hint={HINTS.target} />
          </span>
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
          <span>
            언어 <HelpHint hint={HINTS.language} />
          </span>
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
        <span className="copy-field__label">
          콘텐츠 입력 <HelpHint hint={HINTS.text} />
        </span>
        <div className="textarea-wrap">
          <textarea
            rows={8}
            value={state.input.original_text}
            onChange={(event) => updateInput({ original_text: event.target.value })}
          />
          <small className="character-count character-count--inside" aria-live="polite">
            <strong>{characterCount.toLocaleString()}</strong> / 2,000
          </small>
        </div>
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

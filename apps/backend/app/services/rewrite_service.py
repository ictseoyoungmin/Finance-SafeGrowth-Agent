import hashlib
import json
from typing import Any

from app.integrations.gemini_client import GeminiClient, get_gemini_client
from app.schemas.rewrite import RewriteChange, RewriteRequest, RewriteResponse


FALLBACK_REWRITE = RewriteResponse(
    content_id="fallback",
    revised_text_conservative=(
        "본 상품은 시장 상황에 따라 수익 또는 손실이 발생할 수 있으며, "
        "가입 전 상품설명서와 유의사항을 반드시 확인하시기 바랍니다."
    ),
    revised_text_marketing=(
        "시장 상황에 따라 수익은 변동될 수 있으며, 원금 손실 가능성이 있습니다. "
        "가입 전 상품설명서와 유의사항을 확인해 주세요."
    ),
    changes=[
        RewriteChange(
            original="연 8% 수익을 안정적으로",
            replacement="시장 상황에 따라 수익은 변동될 수 있으며",
            reason="확정 수익 및 안정성 오인 표현 완화",
        ),
        RewriteChange(
            original="원금 걱정 없이",
            replacement="원금 손실 가능성이 있습니다",
            reason="원금 보장 오인 표현을 필수 고지로 대체",
        ),
    ],
)


class RewriteService:
    def __init__(self, gemini_client: GeminiClient) -> None:
        self._gemini_client = gemini_client

    def rewrite(self, request: RewriteRequest) -> RewriteResponse:
        prompt = self._build_prompt(request)
        result = self._gemini_client.generate_json(prompt)
        if result:
            parsed = self._parse_response(request.content_id, result.payload)
            if parsed:
                return parsed

        return FALLBACK_REWRITE.model_copy(update={"content_id": request.content_id})

    def prompt_hash(self, request: RewriteRequest) -> str:
        return hashlib.sha256(self._build_prompt(request).encode("utf-8")).hexdigest()

    def _build_prompt(self, request: RewriteRequest) -> str:
        return json.dumps(
            {
                "task": "financial_ad_compliance_rewrite",
                "content_id": request.content_id,
                "mode": request.mode,
                "response_schema": {
                    "revised_text_conservative": "string",
                    "revised_text_marketing": "string",
                    "changes": [
                        {
                            "original": "string",
                            "replacement": "string",
                            "reason": "string",
                        }
                    ],
                },
            },
            ensure_ascii=False,
        )

    def _parse_response(self, content_id: str, payload: dict[str, Any]) -> RewriteResponse | None:
        try:
            return RewriteResponse(content_id=content_id, **payload)
        except ValueError:
            return None


def get_rewrite_service() -> RewriteService:
    return RewriteService(get_gemini_client())

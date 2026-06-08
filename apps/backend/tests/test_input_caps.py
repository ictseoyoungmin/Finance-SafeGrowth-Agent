"""R-D-1: AnalyzeRequest.original_text has a 5,000-char upper bound."""

import pytest
from pydantic import ValidationError

from app.schemas.compliance import AnalyzeRequest


def _payload(text: str) -> dict:
    return {
        "product_type": "투자상품",
        "channel": "앱 푸시",
        "target_customer": "30대 직장인",
        "language": "ko",
        "original_text": text,
    }


def test_original_text_under_cap_is_accepted() -> None:
    AnalyzeRequest(**_payload("가" * 5000))


def test_original_text_over_cap_is_rejected() -> None:
    with pytest.raises(ValidationError):
        AnalyzeRequest(**_payload("가" * 5001))

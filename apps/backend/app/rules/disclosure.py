"""Disclosure-aware post-processing helpers.

Shared by the rule engine and the analyze service so that downgrade logic
runs once, after both rule and LLM spans have been merged.
"""

import re

from app.schemas.compliance import RiskLevel


# Disclosure phrases that, when found near a risk span, indicate the author
# paired the claim with a required disclaimer. Intentionally specific so that
# negated forms like "원금 손실 없이" do NOT match.
DISCLOSURE_KEYWORDS: tuple[str, ...] = (
    "투자 위험",
    "투자위험",
    "원금 손실 가능",
    "손실 가능성",
    "변동 가능성",
    "변동될 수 있",
    "유의사항",
    "유의하며",
    "유의하시기",
    "상품설명서",
    "예금자보호",
    "운용 책임",
)

DOWNGRADE: dict[RiskLevel, RiskLevel] = {
    RiskLevel.HIGH: RiskLevel.MEDIUM,
    RiskLevel.MEDIUM: RiskLevel.LOW,
    RiskLevel.LOW: RiskLevel.LOW,
}

DOWNGRADE_REASON_SUFFIX = "(인접 고지 문구로 위험도가 한 단계 완화됨)"

_SENTENCE_BOUNDARY = re.compile(r"[.!?\n]+")


def sentence_spans(text: str) -> list[tuple[int, int]]:
    """Split text into sentence (start, end) pairs covering the full text."""
    spans: list[tuple[int, int]] = []
    cursor = 0
    for match in _SENTENCE_BOUNDARY.finditer(text):
        end = match.end()
        if end > cursor:
            spans.append((cursor, end))
        cursor = end
    if cursor < len(text):
        spans.append((cursor, len(text)))
    return spans


def sentence_index(spans: list[tuple[int, int]], position: int) -> int | None:
    for index, (start, end) in enumerate(spans):
        if start <= position < end:
            return index
    return None


def is_disclosure_span(span_text: str) -> bool:
    """True if the span's own text is essentially a disclaimer phrase."""
    return any(keyword in span_text for keyword in DISCLOSURE_KEYWORDS)


def has_disclosure_nearby(
    text: str,
    spans: list[tuple[int, int]],
    index: int,
    *,
    window: int = 1,
) -> bool:
    """Whether any sentence within `index ± window` contains a disclosure phrase."""
    if not spans:
        return False
    lo = max(0, index - window)
    hi = min(len(spans), index + window + 1)
    for start, end in spans[lo:hi]:
        chunk = text[start:end]
        if any(keyword in chunk for keyword in DISCLOSURE_KEYWORDS):
            return True
    return False

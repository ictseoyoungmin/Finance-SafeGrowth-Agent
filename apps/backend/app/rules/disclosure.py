"""Disclosure-aware post-processing helpers.

Shared by the rule engine and the analyze service so that downgrade logic
runs once, after both rule and LLM spans have been merged.
"""

import re

from app.schemas.compliance import FlaggedSpan, RiskLevel


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

# 숫자 사이의 마침표(예: "5.0")는 문장 경계로 인식하지 않는다.
_SENTENCE_BOUNDARY = re.compile(r"(?<!\d)[.!?](?!\d)|\n")


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


def apply_to_spans(text: str, spans: list[FlaggedSpan]) -> list[FlaggedSpan]:
    """Drop disclaimer-only spans and downgrade those near a disclosure.

    Shared by `AnalyzeService` (rule + LLM merge) and `RewriteService`
    (self-validation of generated revisions) so the policy stays in one place.
    """
    if not spans:
        return spans

    sentences = sentence_spans(text)
    cleaned: list[FlaggedSpan] = []
    for span in spans:
        if is_disclosure_span(span.span_text):
            continue

        idx = sentence_index(sentences, span.start)
        if idx is None or not has_disclosure_nearby(text, sentences, idx, window=1):
            cleaned.append(span)
            continue

        downgraded = DOWNGRADE.get(span.severity, span.severity)
        if downgraded == span.severity:
            cleaned.append(span)
            continue

        cleaned.append(
            span.model_copy(
                update={
                    "severity": downgraded,
                    "reason": f"{span.reason} {DOWNGRADE_REASON_SUFFIX}",
                    "confidence": max(0.0, span.confidence - 0.05),
                }
            )
        )
    return cleaned

import re
from dataclasses import dataclass
from re import Pattern

from app.schemas.compliance import FlaggedSpan, RiskLevel


# Disclosure phrases that, when found in the same sentence as a risk match,
# indicate the author has paired the claim with a required disclaimer.
DISCLOSURE_KEYWORDS: tuple[str, ...] = (
    "투자 위험",
    "투자위험",
    "원금 손실 가능",  # 의도적으로 "원금 손실 없이" 같은 부정구는 매치 안 함
    "손실 가능성",
    "변동 가능성",
    "변동될 수 있",
    "유의사항",
    "상품설명서",
    "예금자보호",
    "운용 책임",
)

# Sentence boundary: ., !, ?, !, newline (Korean punctuation also OK).
_SENTENCE_BOUNDARY = re.compile(r"[.!?\n]+")

_DOWNGRADE: dict[RiskLevel, RiskLevel] = {
    RiskLevel.HIGH: RiskLevel.MEDIUM,
    RiskLevel.MEDIUM: RiskLevel.LOW,
    RiskLevel.LOW: RiskLevel.LOW,
}


def _sentence_spans(text: str) -> list[tuple[int, int]]:
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


def _sentence_for(spans: list[tuple[int, int]], position: int) -> tuple[int, int] | None:
    for start, end in spans:
        if start <= position < end:
            return start, end
    return None


@dataclass(frozen=True)
class Rule:
    pattern: Pattern[str]
    risk_category: str
    severity: RiskLevel
    reason: str
    confidence: float


class RuleEngine:
    def __init__(self) -> None:
        self._rules = [
            Rule(
                pattern=re.compile(r"누구나|무조건|반드시|절대|업계\s*최고|최고의?"),
                risk_category="과장 표현",
                severity=RiskLevel.HIGH,
                reason="보편적 수혜 또는 조건 없는 혜택으로 오인될 수 있습니다.",
                confidence=0.92,
            ),
            Rule(
                pattern=re.compile(
                    r"연\s*\d+(?:\.\d+)?\s*%\s*(?:수익|수익률|이자)|"
                    r"(?:확정|고정)\s*(?:수익률|수익|이자)|"
                    r"매월\s*\d+(?:\.\d+)?\s*%\s*(?:지급|수익)"
                ),
                risk_category="확정 수익 오인",
                severity=RiskLevel.HIGH,
                reason="투자상품의 수익률을 확정적으로 받을 수 있는 것처럼 해석될 수 있습니다.",
                confidence=0.95,
            ),
            Rule(
                pattern=re.compile(r"안정적으로|안전하게|위험\s*없이|리스크\s*없이|걱정\s*없이"),
                risk_category="안정성 오인",
                severity=RiskLevel.MEDIUM,
                reason="투자 위험이나 변동 가능성이 낮은 것처럼 오인될 수 있습니다.",
                confidence=0.87,
            ),
            Rule(
                pattern=re.compile(r"원금\s*걱정\s*없이|원금\s*보장|원금\s*손실\s*없(?:음|이)|손실\s*없이"),
                risk_category="원금 보장 오인",
                severity=RiskLevel.HIGH,
                reason="원금 손실 가능성이 없는 것처럼 오인될 수 있습니다.",
                confidence=0.96,
            ),
        ]

    def scan(self, text: str) -> list[FlaggedSpan]:
        hits: list[FlaggedSpan] = []

        for rule in self._rules:
            for match in rule.pattern.finditer(text):
                hits.append(
                    FlaggedSpan(
                        span_text=match.group(0),
                        start=match.start(),
                        end=match.end(),
                        risk_category=rule.risk_category,
                        severity=rule.severity,
                        reason=rule.reason,
                        confidence=rule.confidence,
                    )
                )

        deduped = self._dedupe_overlaps(hits)
        return self._apply_disclosure_downgrade(text, deduped)

    def _apply_disclosure_downgrade(
        self,
        text: str,
        hits: list[FlaggedSpan],
    ) -> list[FlaggedSpan]:
        if not hits:
            return hits

        sentences = _sentence_spans(text)
        adjusted: list[FlaggedSpan] = []
        for hit in hits:
            sentence_span = _sentence_for(sentences, hit.start)
            if sentence_span is None:
                adjusted.append(hit)
                continue
            sentence_text = text[sentence_span[0] : sentence_span[1]]
            if not any(keyword in sentence_text for keyword in DISCLOSURE_KEYWORDS):
                adjusted.append(hit)
                continue

            downgraded_severity = _DOWNGRADE.get(hit.severity, hit.severity)
            if downgraded_severity == hit.severity:
                adjusted.append(hit)
                continue

            adjusted.append(
                hit.model_copy(
                    update={
                        "severity": downgraded_severity,
                        "reason": f"{hit.reason} (같은 문장의 고지 문구로 위험도가 한 단계 완화됨)",
                        "confidence": max(0.0, hit.confidence - 0.05),
                    }
                )
            )
        return adjusted

    def _dedupe_overlaps(self, hits: list[FlaggedSpan]) -> list[FlaggedSpan]:
        selected: list[FlaggedSpan] = []
        for hit in sorted(hits, key=lambda item: (item.start, -(item.end - item.start), item.risk_category)):
            if any(hit.start < existing.end and hit.end > existing.start for existing in selected):
                continue
            selected.append(hit)
        return sorted(selected, key=lambda hit: (hit.start, hit.end, hit.risk_category))

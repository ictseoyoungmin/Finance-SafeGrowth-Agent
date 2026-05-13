import re
from dataclasses import dataclass
from re import Pattern

from app.schemas.compliance import FlaggedSpan, RiskLevel


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
                pattern=re.compile(r"누구나|무조건|반드시"),
                risk_category="과장 표현",
                severity=RiskLevel.HIGH,
                reason="보편적 수혜 또는 조건 없는 혜택으로 오인될 수 있습니다.",
                confidence=0.92,
            ),
            Rule(
                pattern=re.compile(r"연\s*\d+(?:\.\d+)?\s*%\s*수익"),
                risk_category="확정 수익 오인",
                severity=RiskLevel.HIGH,
                reason="투자상품의 수익률을 확정적으로 받을 수 있는 것처럼 해석될 수 있습니다.",
                confidence=0.95,
            ),
            Rule(
                pattern=re.compile(r"안정적으로|안전하게"),
                risk_category="안정성 오인",
                severity=RiskLevel.MEDIUM,
                reason="투자 위험이나 변동 가능성이 낮은 것처럼 오인될 수 있습니다.",
                confidence=0.87,
            ),
            Rule(
                pattern=re.compile(r"원금\s*걱정\s*없이|원금\s*보장"),
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

        return sorted(hits, key=lambda hit: (hit.start, hit.end, hit.risk_category))

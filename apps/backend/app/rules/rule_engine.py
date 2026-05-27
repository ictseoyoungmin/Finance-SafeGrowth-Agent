import re
from dataclasses import dataclass
from re import Pattern

from app.rules.patterns import PATTERN_DEFINITIONS
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
                pattern=re.compile(pattern),
                risk_category=category,
                severity=severity,
                reason=reason,
                confidence=confidence,
            )
            for pattern, category, severity, reason, confidence in PATTERN_DEFINITIONS
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

        return self._dedupe_overlaps(hits)

    def _dedupe_overlaps(self, hits: list[FlaggedSpan]) -> list[FlaggedSpan]:
        selected: list[FlaggedSpan] = []
        for hit in sorted(hits, key=lambda item: (item.start, -(item.end - item.start), item.risk_category)):
            if any(hit.start < existing.end and hit.end > existing.start for existing in selected):
                continue
            selected.append(hit)
        return sorted(selected, key=lambda hit: (hit.start, hit.end, hit.risk_category))

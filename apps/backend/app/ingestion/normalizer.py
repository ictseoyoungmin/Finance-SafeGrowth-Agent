import re
from dataclasses import dataclass

from app.rag.chunker import chunk_text


@dataclass(frozen=True)
class NormalizedRegulation:
    text: str
    chunks: list[str]
    product_type: str
    risk_categories: list[str]


RISK_KEYWORDS = {
    "확정 수익 오인": ("수익률", "확정", "%", "이자", "금리"),
    "안정성 오인": ("안정", "안전", "무위험", "걱정 없이"),
    "원금 보장 오인": ("원금", "보장", "손실"),
    "과장 표현": ("누구나", "최고", "최대", "무조건", "반드시"),
    "불명확한 비용/금리 고지": ("수수료", "비용", "연체", "상환"),
}


def normalize_regulation_text(
    raw_text: str,
    *,
    product_type: str | None = None,
    default_risk_categories: list[str] | None = None,
    max_chars: int = 600,
) -> NormalizedRegulation:
    text = _normalize_whitespace(raw_text)
    inferred_product_type = product_type or _infer_product_type(text)
    categories = _infer_risk_categories(text, default_risk_categories or [])
    chunks = [chunk for chunk in chunk_text(text, max_chars=max_chars) if chunk.strip()]
    return NormalizedRegulation(
        text=text,
        chunks=chunks or ([text] if text else []),
        product_type=inferred_product_type,
        risk_categories=categories,
    )


def _normalize_whitespace(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    compact = "\n".join(line for line in lines if line)
    return re.sub(r"\n{3,}", "\n\n", compact).strip()


def _infer_product_type(text: str) -> str:
    if any(token in text for token in ("투자", "펀드", "ELS", "수익률")):
        return "투자상품"
    if any(token in text for token in ("대출", "상환", "금리")):
        return "대출상품"
    if "카드" in text:
        return "카드"
    return "공통"


def _infer_risk_categories(text: str, defaults: list[str]) -> list[str]:
    categories: list[str] = []
    for category in defaults:
        if category not in categories:
            categories.append(category)
    for category, keywords in RISK_KEYWORDS.items():
        if category not in categories and any(keyword in text for keyword in keywords):
            categories.append(category)
    return categories

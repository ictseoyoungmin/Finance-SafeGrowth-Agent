from app.rag.retriever import get_regulation_retriever


def test_retriever_returns_fallback_docs() -> None:
    retriever = get_regulation_retriever()

    docs = retriever.retrieve(
        risk_categories=["확정 수익 오인", "원금 보장 오인"],
        product_type="투자상품",
    )

    assert len(docs) >= 1
    assert {doc.evidence_id for doc in docs} >= {"doc-demo-001", "doc-demo-002"}

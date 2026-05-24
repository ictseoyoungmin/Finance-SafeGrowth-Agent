from app.repositories.regulation_docs_repo import (
    RegulationDoc,
    RegulationDocsRepository,
    get_regulation_docs_repository,
)


class RegulationRetriever:
    def __init__(self, docs_repository: RegulationDocsRepository) -> None:
        self._docs_repository = docs_repository

    def retrieve(
        self,
        risk_categories: list[str],
        product_type: str,
        limit: int = 5,
        query: str | None = None,
    ) -> list[RegulationDoc]:
        if query:
            return self._docs_repository.vector_search(
                query_text=query,
                risk_categories=risk_categories,
                product_type=product_type,
                limit=limit,
            )
        return self._docs_repository.search(
            risk_categories=risk_categories,
            product_type=product_type,
            limit=limit,
        )


def get_regulation_retriever() -> RegulationRetriever:
    return RegulationRetriever(get_regulation_docs_repository())

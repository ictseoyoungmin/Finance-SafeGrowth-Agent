from uuid import uuid4

from app.schemas.compliance import AnalyzeRequest


class ContentRepository:
    def save_original(self, request: AnalyzeRequest) -> str:
        return f"content-{uuid4()}"


def get_content_repository() -> ContentRepository:
    return ContentRepository()

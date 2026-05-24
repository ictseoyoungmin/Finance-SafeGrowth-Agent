from app.core.config import settings
from app.integrations.llm.base import LlmProvider
from app.integrations.llm.gemini import GeminiLlmProvider
from app.integrations.llm.openai_compatible import OpenAICompatibleLlmProvider


def get_llm_provider() -> LlmProvider:
    if settings.llm_provider.lower() == "openai_compatible":
        return OpenAICompatibleLlmProvider()
    return GeminiLlmProvider()

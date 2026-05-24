from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class AgentLimits:
    max_iterations: int
    deadline_seconds: int


def default_limits() -> AgentLimits:
    return AgentLimits(
        max_iterations=int(settings.agent_max_iterations),
        deadline_seconds=int(settings.agent_deadline_seconds),
    )

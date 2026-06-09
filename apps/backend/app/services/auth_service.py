"""In-memory auth backed by two pre-provisioned accounts.

Avoids a full user/session subsystem for the MVP. Tester credentials are
public demo defaults; the admin password must be supplied via env in any
real deploy where DELETE access matters.
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass

from app.core.config import settings
from app.schemas.auth import AuthProfile


TESTER_PROFILE = AuthProfile(
    id="tester",
    role="tester",
    display_name="테스트 검토자",
    title="Tester",
    team="테스트 팀",
)

ADMIN_PROFILE = AuthProfile(
    id="admin",
    role="admin",
    display_name="김준법 수석",
    title="Compliance Manager",
    team="준법감시팀",
)


@dataclass
class _Session:
    profile: AuthProfile
    expires_at: float


class AuthService:
    """Opaque-token store. Singleton via get_auth_service()."""

    def __init__(self) -> None:
        self._sessions: dict[str, _Session] = {}

    def login(self, user_id: str, password: str) -> tuple[str, AuthProfile] | None:
        profile = self._authenticate(user_id, password)
        if profile is None:
            return None
        token = secrets.token_urlsafe(32)
        self._sessions[token] = _Session(
            profile=profile,
            expires_at=time.time() + settings.auth_token_ttl_seconds,
        )
        return token, profile

    def logout(self, token: str) -> None:
        self._sessions.pop(token, None)

    def lookup(self, token: str) -> AuthProfile | None:
        session = self._sessions.get(token)
        if session is None:
            return None
        if session.expires_at < time.time():
            self._sessions.pop(token, None)
            return None
        return session.profile

    def _authenticate(self, user_id: str, password: str) -> AuthProfile | None:
        if user_id == settings.tester_id and password == settings.tester_password:
            return TESTER_PROFILE
        if (
            user_id == settings.admin_id
            and settings.admin_password
            and password == settings.admin_password
        ):
            return ADMIN_PROFILE
        return None

    # Test hook — reset state without re-importing the module.
    def clear(self) -> None:
        self._sessions.clear()


_AUTH_SERVICE = AuthService()


def get_auth_service() -> AuthService:
    return _AUTH_SERVICE

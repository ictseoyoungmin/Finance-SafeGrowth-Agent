"""FastAPI auth helpers.

Two dependencies:
- require_authenticated: any logged-in user (tester or admin)
- require_admin_role:    admin only. Also honours the legacy
                         x-admin-token header so existing CI/CLI flows
                         (regulation ingest, scripted resets) keep working.
"""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException

from app.core.config import settings
from app.integrations.supabase_client import is_real_value
from app.schemas.auth import AuthProfile
from app.services.auth_service import ADMIN_PROFILE, AuthService, get_auth_service


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip() or None


def require_authenticated(
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthProfile:
    token = _extract_bearer(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    profile = auth_service.lookup(token)
    if profile is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return profile


def require_admin_role(
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthProfile:
    # Legacy static token path: CI / scripted flows authenticate via
    # x-admin-token. Treat a matching token as the admin profile.
    if (
        is_real_value(settings.admin_api_token)
        and x_admin_token == settings.admin_api_token
    ):
        return ADMIN_PROFILE

    token = _extract_bearer(authorization)
    if token is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    profile = auth_service.lookup(token)
    if profile is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    if profile.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required.")
    return profile

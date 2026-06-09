from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.core.auth import require_authenticated
from app.schemas.auth import AuthProfile, LoginRequest, LoginResponse
from app.services.auth_service import AuthService, get_auth_service


router = APIRouter(tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    result = auth_service.login(payload.id, payload.password)
    if result is None:
        raise HTTPException(status_code=401, detail="로그인 정보가 올바르지 않습니다.")
    token, profile = result
    return LoginResponse(token=token, profile=profile)


@router.post("/logout", status_code=204)
def logout(
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> Response:
    if authorization:
        _, _, token = authorization.partition(" ")
        if token:
            auth_service.logout(token.strip())
    return Response(status_code=204)


@router.get("/me", response_model=AuthProfile)
def me(profile: AuthProfile = Depends(require_authenticated)) -> AuthProfile:
    return profile

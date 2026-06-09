from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)


class AuthProfile(BaseModel):
    id: str
    role: str  # "tester" | "admin"
    display_name: str
    title: str
    team: str


class LoginResponse(BaseModel):
    token: str
    profile: AuthProfile

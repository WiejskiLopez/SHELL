from __future__ import annotations

from pydantic import BaseModel


class LoginAuthSessionRequest(BaseModel):
    email: str


class AuthSessionIdResponse(BaseModel):
    id: str


class CurrentUserResponse(BaseModel):
    user_id: str

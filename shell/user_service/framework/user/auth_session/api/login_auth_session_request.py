from __future__ import annotations

from pydantic import BaseModel


class LoginAuthSessionRequest(BaseModel):
    email: str

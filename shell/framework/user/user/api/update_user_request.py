from __future__ import annotations

from pydantic import BaseModel, EmailStr


class UpdateUserRequest(BaseModel):
    email: EmailStr

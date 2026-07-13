from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserDto:
    id: str
    email: str
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CreateUserRequest:
    email: str


@dataclass(frozen=True, slots=True)
class CreateUserResponse:
    id: str


@dataclass(frozen=True, slots=True)
class UpdateUserRequest:
    email: str

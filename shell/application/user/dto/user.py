from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserDto:
    id: str
    code: str
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CreateUserRequest:
    code: str


@dataclass(frozen=True, slots=True)
class CreateUserResponse:
    id: str


@dataclass(frozen=True, slots=True)
class UpdateUserRequest:
    code: str

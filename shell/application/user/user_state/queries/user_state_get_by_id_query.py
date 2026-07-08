from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserStateGetByIdQuery:
    user_state_id: str

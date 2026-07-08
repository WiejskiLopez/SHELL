from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SessionStateGetByIdQuery:
    session_state_id: str

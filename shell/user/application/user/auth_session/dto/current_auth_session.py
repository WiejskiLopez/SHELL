from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CurrentAuthSessionDto:
    auth_session_id: str
    user_id: str

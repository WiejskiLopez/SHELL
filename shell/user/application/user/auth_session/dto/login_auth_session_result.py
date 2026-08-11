from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoginAuthSessionResult:
    auth_session_id: str
    token: str

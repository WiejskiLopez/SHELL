from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetSessionStateByIdQuery:
    session_state_id: str

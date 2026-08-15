from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetUserSkillByIdQuery:
    user_skill_id: str

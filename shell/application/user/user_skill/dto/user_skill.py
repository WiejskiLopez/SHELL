from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class UserSkillDto:
    id: str
    user_id: str
    skill_data: JsonStr
    created_at: datetime | None = None
    updated_at: datetime | None = None


from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserSkillDto:
    id: str
    user_id: str
    skill_data: dict[str, Any]
    created_at: datetime | None = None
    updated_at: datetime | None = None

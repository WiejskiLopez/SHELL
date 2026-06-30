from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.user.value_objects.skill_payload import SkillPayload
    from shell.domain.user.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class UserStateInput:
    user_id: UserId
    payload: SkillPayload
    created_at: CreatedAt

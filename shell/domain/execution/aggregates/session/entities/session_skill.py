from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session.value_objects.session_id import SessionId
from shell.domain.execution.aggregates.session.value_objects.session_skill_id import SessionSkillId
from shell.domain.execution.value_objects.skill_payload import SkillPayload

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class SessionSkill:
    id: SessionSkillId
    session_id: SessionId
    payload: SkillPayload
    created_at: datetime

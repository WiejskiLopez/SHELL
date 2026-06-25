from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.session.value_objects.session_id import SessionId
from shell.domain.execution.aggregates.session.value_objects.session_skill_id import SessionSkillId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class SessionSkillAddedEvent(DomainEvent):
    session_id: SessionId
    skill_id: SessionSkillId

    @classmethod
    def now(cls, session_id: SessionId, skill_id: SessionSkillId, now: datetime) -> SessionSkillAddedEvent:
        return cls(occurred_at=now, session_id=session_id, skill_id=skill_id)

    @classmethod
    def from_payload(cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            session_id=SessionId(payload.get("session_id")),
            skill_id=SessionSkillId(payload.get("skill_id")),
        )

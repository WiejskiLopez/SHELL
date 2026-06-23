from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.session.session_id import SessionId
from shell.domain.platform.events import DomainEvent
from shell.domain.projekt.value_objects.project_id import ProjectId
from shell.domain.user.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class SessionOpenedEvent(DomainEvent):
    session_id: SessionId
    user_id: UserId
    project_id: ProjectId

    @classmethod
    def now(
        cls,
        session_id: SessionId,
        user_id: UserId,
        project_id: ProjectId,
        now: datetime,
    ) -> SessionOpenedEvent:
        return cls(
            occurred_at=now,
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            session_id=SessionId(payload["session_id"]),
            user_id=UserId(payload["user_id"]),
            project_id=ProjectId(payload["project_id"]),
        )

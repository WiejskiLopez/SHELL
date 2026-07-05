from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
    from shell.domain.session.value_objects.project_id_ref import ProjectIdRef
    from shell.domain.session.value_objects.user_id_ref import UserIdRef


@dataclass(frozen=True, slots=True)
class SessionOpenedEvent(DomainEvent):
    session_id: SessionId
    user_id: UserIdRef
    project_id: ProjectIdRef

    @classmethod
    def now(
        cls,
        session_id: SessionId,
        user_id: UserIdRef,
        project_id: ProjectIdRef,
        now: CreatedAt,
    ) -> SessionOpenedEvent:
        return cls(
            occurred_at=now,
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
        )

"""Session aggregate root — V3 with FSM (OPEN -> CLOSED) and skills."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Self

from shell.domain.session.aggregates.session.events.session_closed_event import (
    SessionClosedEvent,
)
from shell.domain.session.aggregates.session.events.session_opened_event import (
    SessionOpenedEvent,
)
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.value_objects.project_id_ref import ProjectIdRef
from shell.domain.session.value_objects.session_status import SessionStatus
from shell.domain.session.value_objects.user_id_ref import UserIdRef
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.updated_at import UpdatedAt


class Session(AggregateRoot[SessionId]):
    """Session aggregate root — V3 with FSM (OPEN -> CLOSED)."""

    __slots__ = (
        "_user_id",
        "_project_id",
        "_status",
        "_opened_at",
        "_closed_at",
    )

    _user_id: UserIdRef
    _project_id: ProjectIdRef
    _status: SessionStatus
    _opened_at: CreatedAt
    _closed_at: UpdatedAt | None

    def __init__(
        self,
        *,
        id: SessionId,
        user_id: UserIdRef,
        project_id: ProjectIdRef,
        status: SessionStatus,
        opened_at: CreatedAt,
        closed_at: UpdatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        self._project_id = project_id
        self._status = status
        self._opened_at = opened_at
        self._closed_at = closed_at

    @classmethod
    def restore(
        cls,
        *,
        id: SessionId,
        user_id: UserIdRef,
        project_id: ProjectIdRef,
        status: SessionStatus,
        opened_at: CreatedAt,
        closed_at: UpdatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            project_id=project_id,
            status=status,
            opened_at=opened_at,
            closed_at=closed_at,
        )

    # --- V3 properties ---

    @property
    def user_id(self) -> UserIdRef:
        return self._user_id

    @property
    def project_id(self) -> ProjectIdRef:
        return self._project_id

    @property
    def session_status(self) -> SessionStatus:
        return self._status

    @property
    def opened_at(self) -> CreatedAt:
        return self._opened_at

    @property
    def closed_at(self) -> UpdatedAt | None:
        return self._closed_at

    # --- Legacy deprecated properties ---

    @property
    def goal(self) -> str:
        """Deprecated: goal was replaced by structured state_inputs."""
        return ""

    @property
    def status(self) -> str:
        """Returns lowercase status string for backward compat."""
        return self._status.value.lower()

    # --- Factory ---

    @classmethod
    def open(
        cls,
        id_: SessionId,
        user_id: UserIdRef | None = None,
        project_id: ProjectIdRef | None = None,
        now: CreatedAt | None = None,
        goal: str | None = None,  # legacy
    ) -> Session:
        if user_id is None:
            user_id = UserIdRef.generate()
        if project_id is None:
            project_id = ProjectIdRef.generate()
        if now is None:
            now = CreatedAt.now()
        elif isinstance(now, datetime):
            now = CreatedAt.from_datetime(now)
        session = cls(
            id=id_,
            user_id=user_id,
            project_id=project_id,
            status=SessionStatus.OPEN,
            opened_at=now,
        )
        session.append_event(SessionOpenedEvent.now(session.id, user_id, project_id, now=now))
        return session

    # --- Methods ---

    def close(self, now: UpdatedAt) -> None:
        if self._status != SessionStatus.OPEN:
            raise ValueError(f"Cannot close session in status {self._status!r}")
        self._status = SessionStatus.CLOSED
        self._closed_at = now
        self.append_event(SessionClosedEvent.now(self._id, now=CreatedAt.from_datetime(now.value)))

"""Session aggregate root — V3 with FSM (OPEN -> CLOSED) and skills."""

from __future__ import annotations

from typing import Self

from shell.domain.session.aggregates.session.events.session_closed_event import (
    SessionClosedEvent,
)
from shell.domain.session.aggregates.session.events.session_deleted_event import SessionDeletedEvent
from shell.domain.session.aggregates.session.events.session_opened_event import (
    SessionOpenedEvent,
)
from shell.domain.session.aggregates.session.events.session_updated_event import SessionUpdatedEvent
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.value_objects.project_id_ref import ProjectIdRef
from shell.domain.session.value_objects.session_status import SessionStatus
from shell.domain.session.value_objects.user_id_ref import UserIdRef
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt


class Session(AggregateRoot[SessionId]):
    """Session aggregate root — V3 with FSM (OPEN -> CLOSED)."""

    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
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
    _closed_at: UpdatedAt
    _created_at: CreatedAt | None
    _updated_at: UpdatedAt
    _deleted_at: DeletedAt

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
        self._closed_at = UpdatedAt(value=None) if closed_at is None else closed_at
        self._created_at = opened_at
        self._updated_at = UpdatedAt(value=None)
        self._deleted_at = DeletedAt(value=None)

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
        session = cls(
            id=id_,
            user_id=user_id,
            project_id=project_id,
            status=SessionStatus.OPEN,
            opened_at=now,
        )
        session.append_event(
            SessionOpenedEvent.now(
                session.id, user_id, project_id, now=OccurredAt.from_datetime(now.value)
            )
        )
        return session

    # --- Methods ---

    def close(self, now: UpdatedAt) -> None:
        if self._status != SessionStatus.OPEN:
            raise DomainError(f"Cannot close session in status {self._status!r}")
        self._status = SessionStatus.CLOSED
        self._closed_at = now
        self.append_event(SessionClosedEvent.now(self._id, now=OccurredAt.from_datetime(now.value)))

    @classmethod
    def restore(
        cls,
        *,
        id: SessionId,
        deleted_at: DeletedAt | None = None,
        closed_at: UpdatedAt | None = None,
        opened_at: CreatedAt,
        user_id: UserIdRef,
        project_id: ProjectIdRef,
        status: SessionStatus,
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

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            SessionUpdatedEvent.now(
                session_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            SessionDeletedEvent.now(
                session_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

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
    def closed_at(self) -> UpdatedAt:
        return self._closed_at

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    # --- Legacy deprecated properties ---

    @property
    def goal(self) -> str:
        """Deprecated: goal was replaced by structured state_inputs."""
        return ""

    # --- Factory ---

    @classmethod
    def _new(
        cls,
        id_: SessionId,
        now: OccurredAt | None = None,
        user_id: UserIdRef | None = None,
        project_id: ProjectIdRef | None = None,
        goal: str | None = None,  # legacy
    ) -> Session:
        if user_id is None:
            user_id = UserIdRef.generate()
        if project_id is None:
            project_id = ProjectIdRef.generate()
        if now is None:
            now = OccurredAt.now()
        session = cls(
            id=id_,
            user_id=user_id,
            project_id=project_id,
            status=SessionStatus.OPEN,
            opened_at=CreatedAt.from_datetime(now.value),
        )
        session.append_event(SessionOpenedEvent.now(session.id, user_id, project_id, now=now))
        return session

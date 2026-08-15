"""Session aggregate root — V3 with FSM (OPEN -> CLOSED) and skills."""

from __future__ import annotations

from typing import Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.session_service.domain.session.aggregates.session.events.session_changed_event import (
    SessionChangedEvent,
)
from shell.session_service.domain.session.aggregates.session.events.session_closed_event import (
    SessionClosedEvent,
)
from shell.session_service.domain.session.aggregates.session.events.session_deleted_event import (
    SessionDeletedEvent,
)
from shell.session_service.domain.session.aggregates.session.events.session_opened_event import (
    SessionOpenedEvent,
)
from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
    SessionId,
)
from shell.session_service.domain.session.value_objects.session_status import SessionStatus
from shell.session_service.domain.session.value_objects.user_id_ref import UserIdRef


class Session(AggregateRoot[SessionId]):
    """Session aggregate root — V3 with FSM (OPEN -> CLOSED)."""

    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_user_id",
        "_status",
        "_opened_at",
        "_closed_at",
    )

    _user_id: UserIdRef
    _status: SessionStatus
    _opened_at: CreatedAt
    _closed_at: ChangedAt
    _created_at: CreatedAt
    _changed_at: ChangedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        *,
        id: SessionId,
        user_id: UserIdRef,
        status: SessionStatus,
        opened_at: CreatedAt,
        closed_at: ChangedAt = NONE_CHANGED_AT,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        self._status = status
        self._opened_at = opened_at
        self._closed_at = closed_at
        self._created_at = opened_at
        self._changed_at = NONE_CHANGED_AT
        self._deleted_at = NONE_DELETED_AT

    @classmethod
    def open(
        cls,
        id_: SessionId,
        user_id: UserIdRef | None = None,
        now: CreatedAt | None = None,
        goal: str | None = None,  # legacy
    ) -> Session:
        if user_id is None:
            user_id = UserIdRef.generate()
        if now is None:
            now = CreatedAt.now()
        session = cls(
            id=id_,
            user_id=user_id,
            status=SessionStatus.OPEN,
            opened_at=now,
        )
        session.append_event(
            SessionOpenedEvent.now(session.id, user_id, now=OccurredAt.from_datetime(now.value))
        )
        return session

    # --- Methods ---

    def close(self, now: ChangedAt) -> None:
        if self._status != SessionStatus.OPEN:
            raise DomainError(f"Cannot close session in status {self._status!r}")
        self._status = SessionStatus.CLOSED
        self._closed_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(SessionClosedEvent.now(self._id, now=OccurredAt.from_datetime(now.value)))

    def change(self, now: OccurredAt) -> None:
        if self._status != SessionStatus.OPEN:
            raise DomainError(f"Cannot change session in status {self._status!r}")
        self._change(now=now)

    def delete(self, now: DeletedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Session already deleted")
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SessionDeletedEvent.now(
                session_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SessionChangedEvent.now(
                session_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SessionDeletedEvent.now(
                session_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @classmethod
    def restore(
        cls,
        *,
        id: SessionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        opened_at: CreatedAt,
        closed_at: ChangedAt = NONE_CHANGED_AT,
        user_id: UserIdRef,
        status: SessionStatus,
    ) -> Self:
        session = cls(
            id=id,
            user_id=user_id,
            status=status,
            opened_at=opened_at,
            closed_at=closed_at,
        )
        session._created_at = created_at
        session._changed_at = changed_at
        session._deleted_at = deleted_at
        return session

    @property
    def user_id(self) -> UserIdRef:
        return self._user_id

    @property
    def session_status(self) -> SessionStatus:
        return self._status

    @property
    def opened_at(self) -> CreatedAt:
        return self._opened_at

    @property
    def closed_at(self) -> ChangedAt:
        return self._closed_at

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

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
        goal: str | None = None,  # legacy
    ) -> Session:
        if user_id is None:
            user_id = UserIdRef.generate()
        if now is None:
            now = OccurredAt.now()
        session = cls(
            id=id_,
            user_id=user_id,
            status=SessionStatus.OPEN,
            opened_at=CreatedAt.from_datetime(now.value),
        )
        session.append_event(SessionOpenedEvent.now(session.id, user_id, now=now))
        return session

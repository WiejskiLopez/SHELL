from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.session_execution.events.session_execution_changed_event import (
    SessionExecutionChangedEvent,
)
from shell.execution_service.domain.execution.aggregates.session_execution.events.session_execution_created_event import (
    SessionExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.session_execution.events.session_execution_deleted_event import (
    SessionExecutionDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
        SessionIdRef,
    )
    from shell.execution_service.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )


class SessionExecution(AggregateRoot[SessionExecutionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_user_execution_id",
        "_session_id",
    )

    _user_execution_id: UserExecutionId | None
    _session_id: SessionIdRef | None
    _created_at: CreatedAt
    _changed_at: ChangedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        *,
        id: SessionExecutionId,
        created_at: CreatedAt,
        user_execution_id: UserExecutionId | None = None,
        session_id: SessionIdRef | None = None,
    ) -> None:
        super().__init__(id)
        self._user_execution_id = user_execution_id
        self._session_id = session_id
        if created_at is not None:
            self._created_at = created_at
        self._changed_at = NONE_CHANGED_AT
        self._deleted_at = NONE_DELETED_AT

    @classmethod
    def create(
        cls,
        *,
        id_: SessionExecutionId,
        now: CreatedAt,
        session_id: SessionIdRef,
    ) -> SessionExecution:
        return cls._new(id_=id_, session_id=session_id, now=OccurredAt.from_datetime(now.value))

    @classmethod
    def restore(
        cls,
        *,
        id: SessionExecutionId,
        created_at: CreatedAt,
        user_execution_id: UserExecutionId | None = None,
        session_id: SessionIdRef | None = None,
    ) -> Self:
        return cls(
            id=id,
            user_execution_id=user_execution_id,
            session_id=session_id,
            created_at=created_at,
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SessionExecutionChangedEvent.now(
                session_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SessionExecutionDeletedEvent.now(
                session_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def user_execution_id(self) -> UserExecutionId | None:
        return self._user_execution_id

    @property
    def session_id(self) -> SessionIdRef | None:
        return self._session_id

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @classmethod
    def _new(
        cls,
        *,
        id_: SessionExecutionId,
        now: OccurredAt,
        session_id: SessionIdRef,
    ) -> SessionExecution:
        session_execution = cls(
            id=id_,
            session_id=session_id,
            created_at=CreatedAt.from_datetime(now.value),
        )
        session_execution.append_event(
            SessionExecutionCreatedEvent.now(
                session_execution_id=id_,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return session_execution

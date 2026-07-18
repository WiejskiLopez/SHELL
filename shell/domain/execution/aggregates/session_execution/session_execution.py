from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
        SessionIdRef,
    )
    from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


from shell.domain.execution.aggregates.session_execution.events.session_execution_created_event import (
    SessionExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.session_execution.events.session_execution_deleted_event import (
    SessionExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.session_execution.events.session_execution_updated_event import (
    SessionExecutionUpdatedEvent,
)


class SessionExecution(AggregateRoot[SessionExecutionId]):
    __slots__ = (
        "_updated_at",
        "_user_execution_id",
        "_session_id",
        "_created_at",
        "_deleted_at",
    )

    _user_execution_id: UserExecutionId | None
    _session_id: SessionIdRef | None
    _created_at: CreatedAt
    _updated_at: UpdatedAt | None
    _deleted_at: DeletedAt | None

    def __init__(
        self,
        *,
        id: SessionExecutionId,
        user_execution_id: UserExecutionId | None = None,
        session_id: SessionIdRef | None = None,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._user_execution_id = user_execution_id
        self._session_id = session_id
        if created_at is not None:
            self._created_at = created_at
        self._updated_at = None
        self._deleted_at = None

    @classmethod
    def create(
        cls,
        *,
        id_: SessionExecutionId,
        session_id: SessionIdRef,
        now: CreatedAt,
    ) -> SessionExecution:
        return cls._new(id_=id_, session_id=session_id, now=now)

    @classmethod
    def restore(
        cls,
        *,
        id: SessionExecutionId,
        user_execution_id: UserExecutionId | None = None,
        session_id: SessionIdRef | None = None,
        created_at: CreatedAt,
    ) -> Self:
        return cls(
            id=id,
            user_execution_id=user_execution_id,
            session_id=session_id,
            created_at=created_at,
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            SessionExecutionUpdatedEvent.now(
                session_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            SessionExecutionDeletedEvent.now(
                session_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    @property
    def user_execution_id(self) -> UserExecutionId | None:
        return self._user_execution_id

    @property
    def session_id(self) -> SessionIdRef | None:
        return self._session_id

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @classmethod
    def _new(
        cls,
        *,
        id_: SessionExecutionId,
        session_id: SessionIdRef,
        now: CreatedAt,
    ) -> SessionExecution:
        session_execution = cls(
            id=id_,
            session_id=session_id,
            created_at=now,
        )
        session_execution.append_event(
            SessionExecutionCreatedEvent.now(
                session_execution_id=id_,
                now=now,
            )
        )
        return session_execution

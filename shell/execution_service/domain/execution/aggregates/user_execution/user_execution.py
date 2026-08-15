from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.user_execution.events.user_execution_changed_event import (
    UserExecutionChangedEvent,
)
from shell.execution_service.domain.execution.aggregates.user_execution.events.user_execution_created_event import (
    UserExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.user_execution.events.user_execution_deleted_event import (
    UserExecutionDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.user_execution.value_objects.user_id_ref import (
        UserIdRef,
    )


class UserExecution(AggregateRoot[UserExecutionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_user_id",
    )

    _user_id: UserIdRef | None
    _created_at: CreatedAt
    _changed_at: ChangedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        *,
        id: UserExecutionId,
        created_at: CreatedAt,
        user_id: UserIdRef | None = None,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        if created_at is not None:
            self._created_at = created_at
        self._changed_at = NONE_CHANGED_AT
        self._deleted_at = NONE_DELETED_AT

    @classmethod
    def create(
        cls,
        *,
        id_: UserExecutionId,
        now: CreatedAt,
        user_id: UserIdRef,
    ) -> UserExecution:
        return cls._new(id_=id_, user_id=user_id, now=OccurredAt.from_datetime(now.value))

    @classmethod
    def restore(
        cls,
        *,
        id: UserExecutionId,
        created_at: CreatedAt,
        user_id: UserIdRef | None = None,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            created_at=created_at,
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            UserExecutionChangedEvent.now(
                user_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            UserExecutionDeletedEvent.now(
                user_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def user_id(self) -> UserIdRef | None:
        return self._user_id

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
        id_: UserExecutionId,
        now: OccurredAt,
        user_id: UserIdRef,
    ) -> UserExecution:
        user_execution = cls(
            id=id_,
            user_id=user_id,
            created_at=CreatedAt.from_datetime(now.value),
        )
        user_execution.append_event(
            UserExecutionCreatedEvent.now(
                user_execution_id=id_,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return user_execution

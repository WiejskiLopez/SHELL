from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.user_execution.events.user_execution_created_event import (
    UserExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.user_execution.events.user_execution_deleted_event import (
    UserExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.user_execution.events.user_execution_updated_event import (
    UserExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution.value_objects.user_id_ref import UserIdRef


class UserExecution(AggregateRoot[UserExecutionId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_user_id",
    )

    _user_id: UserIdRef | None
    _created_at: CreatedAt
    _updated_at: UpdatedAt
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
        self._updated_at = UpdatedAt(value=None)
        self._deleted_at = DeletedAt(value=None)

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

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            UserExecutionUpdatedEvent.now(
                user_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
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
    def created_at(self) -> CreatedAt | None:
        return self._created_at

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

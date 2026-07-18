from __future__ import annotations

from typing import TYPE_CHECKING, Self

from execution.aggregates.user_execution.events.userexecution_deleted_event import (
    UserExecutionDeletedEvent,
)
from execution.aggregates.user_execution.events.userexecution_updated_event import (
    UserExecutionUpdatedEvent,
)

from shell.domain.execution.aggregates.user_execution.events.user_execution_created_event import (
    UserExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution.value_objects.user_id_ref import UserIdRef
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


class UserExecution(AggregateRoot[UserExecutionId]):
    __slots__ = (
        "_updated_at",
        "_user_id",
        "_created_at",
    )

    _user_id: UserIdRef | None
    _created_at: CreatedAt
    def __init__(
        self,
        *,
        id: UserExecutionId,
        user_id: UserIdRef | None = None,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        if created_at is not None:
            self._created_at = created_at


    @classmethod
    def create(
        cls,
        *,
        id_: UserExecutionId,
        user_id: UserIdRef,
        now: CreatedAt,
    ) -> UserExecution:
        return cls._new(id_=id_, user_id=user_id, now=now)

    @classmethod
    def restore(
        cls,
        *,
        id: UserExecutionId,
        user_id: UserIdRef | None = None,
        created_at: CreatedAt,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            created_at=created_at,
        )


    @classmethod
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            UserExecutionUpdatedEvent.now(
                userexecution_id=self._id,
                now=now,
            )
        )



    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            UserExecutionDeletedEvent.now(
                userexecution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
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
        user_id: UserIdRef,
        now: CreatedAt,
    ) -> UserExecution:
        user_execution = cls(
            id=id_,
            user_id=user_id,
            created_at=now,
        )
        user_execution.append_event(
            UserExecutionCreatedEvent.now(
                user_execution_id=id_,
                now=now,
            )
        )
        return user_execution

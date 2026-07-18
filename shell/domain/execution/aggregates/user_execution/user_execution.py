from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.user_execution.events.user_execution_created_event import (
    UserExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.platform.domain.base import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution.value_objects.user_id_ref import UserIdRef
    from shell.platform.domain.value_objects.created_at import CreatedAt


class UserExecution(AggregateRoot[UserExecutionId]):
    __slots__ = (
        "_updated_at",
        "_user_id",
        "_created_at",
    )

    _user_id: UserIdRef | None
    _created_at: CreatedAt | None

    def __init__(
        self,
        *,
        id: UserExecutionId,
        user_id: UserIdRef | None = None,
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        if created_at is not None:
            self._created_at = created_at

    @classmethod
    def restore(
        cls,
        *,
        id: UserExecutionId,
        user_id: UserIdRef | None = None,
        created_at: CreatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            created_at=created_at,
        )


    @classmethod
    def _update(cls) -> None:
        raise NotImplementedError("_update() not yet implemented")


    @classmethod
    def _new(cls) -> UserExecution:
        raise NotImplementedError("_new() not yet implemented")

    def _delete(self) -> None:
        raise NotImplementedError("_delete() not yet implemented")

    @property
    def user_id(self) -> UserIdRef | None:
        return self._user_id

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @classmethod
    def create(
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

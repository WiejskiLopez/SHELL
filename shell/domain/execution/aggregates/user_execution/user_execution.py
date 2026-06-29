from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.value_objects.user_id_ref import UserIdRef


class UserExecution(AggregateRoot[UserExecutionId]):
    __slots__ = (
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
        user_id: UserIdRef | None = None,
        now: datetime,
    ) -> UserExecution:
        user_execution = cls(
            id=id_,
            user_id=user_id,
            created_at=CreatedAt.from_datetime(now),
        )
        from shell.domain.execution.aggregates.user_execution.events.user_execution_created_event import (
            UserExecutionCreatedEvent,
        )

        user_execution.append_event(
            UserExecutionCreatedEvent.now(
                user_execution_id=id_,
                now=CreatedAt.from_datetime(now),
            )
        )
        return user_execution


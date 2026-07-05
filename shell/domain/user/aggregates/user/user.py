from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.value_objects.identity import Identity
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.domain.user.aggregates.user.events.user_deleted_event import UserDeletedEvent
from shell.domain.user.aggregates.user.events.user_disabled_event import UserDisabledEvent
from shell.domain.user.aggregates.user.events.user_enabled_event import UserEnabledEvent
from shell.domain.user.aggregates.user.events.user_updated_event import UserUpdatedEvent
from shell.domain.user.value_objects.user_code import UserCode
from shell.domain.user.value_objects.user_id import UserId
from shell.domain.user.value_objects.user_status import UserStatus

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.user.aggregates.user.entities.user_skill import UserSkill
    from shell.domain.user.aggregates.user.entities.user_state_input import UserStateInput
    from shell.domain.user.aggregates.user.entities.user_state_output import UserStateOutput


class User(AggregateRoot[UserId]):
    __slots__ = (
        "_code",
        "_identity",
        "_status",
        "_skills",
        "_state_inputs",
        "_state_outputs",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    _code: UserCode
    _identity: Identity
    _status: UserStatus
    _skills: list[UserSkill]
    _state_inputs: list[UserStateInput]
    _state_outputs: list[UserStateOutput]
    _created_at: CreatedAt | None
    _updated_at: UpdatedAt | None
    _deleted_at: DeletedAt | None

    def __init__(
        self,
        *,
        id: UserId,
        code: UserCode,
        identity: Identity | None = None,
        status: UserStatus = UserStatus.ACTIVE,
        skills: list[UserSkill] | None = None,
        state_inputs: list[UserStateInput] | None = None,
        state_outputs: list[UserStateOutput] | None = None,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._code = code
        self._identity = identity or Identity({})
        self._status = status
        self._skills = list(skills) if skills else []
        self._state_inputs = list(state_inputs) if state_inputs else []
        self._state_outputs = list(state_outputs) if state_outputs else []
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: UserId,
        code: UserCode,
        identity: Identity | None = None,
        status: UserStatus = UserStatus.ACTIVE,
        skills: list[UserSkill] | None = None,
        state_inputs: list[UserStateInput] | None = None,
        state_outputs: list[UserStateOutput] | None = None,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            code=code,
            identity=identity,
            status=status,
            skills=skills,
            state_inputs=state_inputs,
            state_outputs=state_outputs,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    @property
    def code(self) -> UserCode:
        return self._code

    @property
    def identity(self) -> Identity:
        return self._identity

    @property
    def status(self) -> UserStatus:
        return self._status

    @property
    def skills(self) -> tuple[UserSkill, ...]:
        return tuple(self._skills)

    @property
    def state_inputs(self) -> tuple[UserStateInput, ...]:
        return tuple(self._state_inputs)

    @property
    def state_outputs(self) -> tuple[UserStateOutput, ...]:
        return tuple(self._state_outputs)

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt | None:
        return self._deleted_at

    @property
    def is_deleted(self) -> bool:
        return self._deleted_at is not None

    def update(self, code: UserCode, now: datetime) -> None:
        self._code = code
        self._updated_at = UpdatedAt.from_datetime(now)
        self.append_event(UserUpdatedEvent.now(user_id=self._id, now=CreatedAt.from_datetime(now)))

    def delete(self, now: datetime) -> None:
        self._deleted_at = DeletedAt.from_datetime(now)
        self._updated_at = UpdatedAt.from_datetime(now)
        self.append_event(UserDeletedEvent.now(user_id=self._id, now=CreatedAt.from_datetime(now)))

    def enable(self, now: datetime) -> None:
        if self._status != UserStatus.DISABLED:
            raise ValueError(f"Cannot enable user in status {self._status!r}")
        self._status = UserStatus.ACTIVE
        self.append_event(UserEnabledEvent.now(self._id, now=CreatedAt.from_datetime(now)))

    def disable(self, now: datetime) -> None:
        if self._status != UserStatus.ACTIVE:
            raise ValueError(f"Cannot disable user in status {self._status!r}")
        self._status = UserStatus.DISABLED
        self.append_event(UserDisabledEvent.now(self._id, now=CreatedAt.from_datetime(now)))

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.user.aggregates.user.events.user_disabled_event import UserDisabledEvent
from shell.domain.user.aggregates.user.events.user_enabled_event import UserEnabledEvent
from shell.domain.user.aggregates.user.exceptions.invalid_user_transition import (
    InvalidUserTransition,
)
from shell.domain.user.value_objects.user_id import UserId
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.user.value_objects.user_status import UserStatus

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.value_objects.identity import Identity
    from shell.domain.user.aggregates.user.entities.user_skill import UserSkill
    from shell.domain.user.aggregates.user.entities.user_state_input import UserStateInput
    from shell.domain.user.aggregates.user.entities.user_state_output import UserStateOutput


class User(AggregateRoot[UserId]):
    __slots__ = (
        "_identity",
        "_status",
        "_skills",
        "_state_inputs",
        "_state_outputs",
    )

    _identity: Identity
    _status: UserStatus
    _skills: list[UserSkill]
    _state_inputs: list[UserStateInput]
    _state_outputs: list[UserStateOutput]

    def __init__(
        self,
        *,
        id: UserId,
        identity: Identity,
        status: UserStatus = UserStatus.ACTIVE,
        skills: list[UserSkill] | None = None,
        state_inputs: list[UserStateInput] | None = None,
        state_outputs: list[UserStateOutput] | None = None,
    ) -> None:
        super().__init__(id)
        self._identity = identity
        self._status = status
        self._skills = list(skills) if skills else []
        self._state_inputs = list(state_inputs) if state_inputs else []
        self._state_outputs = list(state_outputs) if state_outputs else []

    @classmethod
    def restore(
        cls,
        *,
        id: UserId,
        identity: Identity,
        status: UserStatus = UserStatus.ACTIVE,
        skills: list[UserSkill] | None = None,
        state_inputs: list[UserStateInput] | None = None,
        state_outputs: list[UserStateOutput] | None = None,
    ) -> Self:
        return cls(
            id=id,
            identity=identity,
            status=status,
            skills=skills,
            state_inputs=state_inputs,
            state_outputs=state_outputs,
        )

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

    def enable(self, now: datetime) -> None:
        if self._status != UserStatus.DISABLED:
            raise InvalidUserTransition(
                f"Cannot enable user in status {self._status!r}"
            )
        self._status = UserStatus.ACTIVE
        self.append_event(UserEnabledEvent.now(self._id, now=CreatedAt.from_datetime(now)))

    def disable(self, now: datetime) -> None:
        if self._status != UserStatus.ACTIVE:
            raise InvalidUserTransition(
                f"Cannot disable user in status {self._status!r}"
            )
        self._status = UserStatus.DISABLED
        self.append_event(UserDisabledEvent.now(self._id, now=CreatedAt.from_datetime(now)))

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.user_service.domain.user.aggregates.user.events.user_changed_event import (
    UserChangedEvent,
)
from shell.user_service.domain.user.aggregates.user.events.user_created_event import (
    UserCreatedEvent,
)
from shell.user_service.domain.user.aggregates.user.events.user_deleted_event import (
    UserDeletedEvent,
)
from shell.user_service.domain.user.aggregates.user.exceptions.user_already_deleted_error import (
    UserAlreadyDeletedError,
)
from shell.user_service.domain.user.aggregates.user.exceptions.user_state_transition_error import (
    UserStateTransitionError,
)
from shell.user_service.domain.user.value_objects.user_id import UserId
from shell.user_service.domain.user.value_objects.user_status import UserStatus

if TYPE_CHECKING:
    from shell.user_service.domain.user.value_objects.user_email import UserEmail


class User(AggregateRoot[UserId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_email",
        "_status",
    )

    _email: UserEmail
    _status: UserStatus
    _created_at: CreatedAt
    _changed_at: ChangedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        *,
        id: UserId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        email: UserEmail,
        status: UserStatus,
    ) -> None:
        super().__init__(id)
        self._email = email
        self._status = status
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

    @classmethod
    def _new(
        cls,
        *,
        id: UserId,
        now: OccurredAt,
        email: UserEmail,
    ) -> Self:
        user = cls(
            id=id,
            email=email,
            status=UserStatus.ACTIVE,
            created_at=CreatedAt.from_datetime(now.value),
        )
        user.append_event(UserCreatedEvent.now(user_id=id, now=now))
        return user

    @classmethod
    def create(
        cls,
        *,
        id: UserId,
        now: CreatedAt,
        email: UserEmail,
    ) -> User:
        return cls._new(id=id, email=email, now=OccurredAt.from_datetime(now.value))

    @classmethod
    def restore(
        cls,
        *,
        id: UserId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        email: UserEmail,
        status: UserStatus,
    ) -> Self:
        return cls(
            id=id,
            email=email,
            status=status,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            UserDeletedEvent.now(
                user_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            UserChangedEvent.now(
                user_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def email(self) -> UserEmail:
        return self._email

    @property
    def status(self) -> UserStatus:
        return self._status

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    @property
    def is_deleted(self) -> bool:
        return self._deleted_at.value is not None

    def change(self, email: UserEmail, now: OccurredAt) -> None:
        if self._deleted_at.value is not None:
            raise UserAlreadyDeletedError("Cannot change a deleted user")
        self._email = email
        self._change(now=now)

    def delete(self, now: DeletedAt) -> None:
        if self._deleted_at.value is not None:
            raise UserAlreadyDeletedError("User already deleted")
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            UserDeletedEvent.now(user_id=self._id, now=OccurredAt.from_datetime(now.value))
        )

    def enable(self) -> None:
        if self._deleted_at.value is not None:
            raise UserAlreadyDeletedError("Cannot enable a deleted user")
        if self._status != UserStatus.DISABLED:
            raise UserStateTransitionError(f"Cannot enable user in status {self._status!r}")
        self._status = UserStatus.ACTIVE

    def disable(self) -> None:
        if self._deleted_at.value is not None:
            raise UserAlreadyDeletedError("Cannot disable a deleted user")
        if self._status != UserStatus.ACTIVE:
            raise UserStateTransitionError(f"Cannot disable user in status {self._status!r}")
        self._status = UserStatus.DISABLED

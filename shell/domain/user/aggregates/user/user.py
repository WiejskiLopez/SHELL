from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.user.aggregates.user.events.user_created_event import UserCreatedEvent
from shell.domain.user.aggregates.user.events.user_deleted_event import UserDeletedEvent
from shell.domain.user.aggregates.user.events.user_updated_event import UserUpdatedEvent
from shell.domain.user.value_objects.user_id import UserId
from shell.domain.user.value_objects.user_status import UserStatus
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt

if TYPE_CHECKING:
    from shell.domain.user.value_objects.user_email import UserEmail


class User(AggregateRoot[UserId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_email",
        "_status",
    )

    _email: UserEmail
    _status: UserStatus
    _created_at: CreatedAt
    _updated_at: UpdatedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        *,
        id: UserId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        email: UserEmail,
        status: UserStatus = UserStatus.ACTIVE,
    ) -> None:
        super().__init__(id)
        self._email = email
        self._status = status
        self._created_at = created_at
        self._updated_at = updated_at
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
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        email: UserEmail,
        status: UserStatus = UserStatus.ACTIVE,
    ) -> Self:
        return cls(
            id=id,
            email=email,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            UserDeletedEvent.now(
                user_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            UserUpdatedEvent.now(
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
    def updated_at(self) -> UpdatedAt:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    @property
    def is_deleted(self) -> bool:
        return self._deleted_at.value is not None

    def update(self, email: UserEmail, now: UpdatedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot update a deleted user")
        self._email = email
        self._updated_at = now
        self.append_event(
            UserUpdatedEvent.now(user_id=self._id, now=OccurredAt.from_datetime(now.value))
        )

    def delete(self, now: DeletedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("User already deleted")
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            UserDeletedEvent.now(user_id=self._id, now=OccurredAt.from_datetime(now.value))
        )

    def enable(self) -> None:
        if self._status != UserStatus.DISABLED:
            raise DomainError(f"Cannot enable user in status {self._status!r}")
        self._status = UserStatus.ACTIVE

    def disable(self) -> None:
        if self._status != UserStatus.ACTIVE:
            raise DomainError(f"Cannot disable user in status {self._status!r}")
        self._status = UserStatus.DISABLED

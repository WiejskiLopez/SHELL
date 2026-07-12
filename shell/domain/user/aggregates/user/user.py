from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.user.aggregates.user.events.user_created_event import UserCreatedEvent
from shell.domain.user.aggregates.user.events.user_deleted_event import UserDeletedEvent
from shell.domain.user.aggregates.user.events.user_updated_event import UserUpdatedEvent
from shell.domain.user.value_objects.user_id import UserId
from shell.domain.user.value_objects.user_status import UserStatus
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.user.value_objects.user_email import UserEmail
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


class User(AggregateRoot[UserId]):
    __slots__ = (
        "_email",
        "_status",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    _email: UserEmail
    _status: UserStatus
    _created_at: CreatedAt | None
    _updated_at: UpdatedAt | None
    _deleted_at: DeletedAt | None

    def __init__(
        self,
        *,
        id: UserId,
        email: UserEmail,
        status: UserStatus = UserStatus.ACTIVE,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._email = email
        self._status = status
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def create(
        cls,
        *,
        id: UserId,
        email: UserEmail,
        now: CreatedAt,
    ) -> Self:
        created_at = now
        user = cls(
            id=id,
            email=email,
            created_at=created_at,
        )
        user.append_event(UserCreatedEvent.now(user_id=id, now=created_at))
        return user

    @classmethod
    def restore(
        cls,
        *,
        id: UserId,
        email: UserEmail,
        status: UserStatus = UserStatus.ACTIVE,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            email=email,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    @property
    def email(self) -> UserEmail:
        return self._email

    @property
    def status(self) -> UserStatus:
        return self._status

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

    def update(self, email: UserEmail, now: UpdatedAt) -> None:
        if self._deleted_at is not None:
            raise ValueError("Cannot update a deleted user")
        self._email = email
        self._updated_at = now
        self.append_event(UserUpdatedEvent.now(user_id=self._id, now=CreatedAt.from_datetime(now.value)))

    def delete(self, now: DeletedAt) -> None:
        if self._deleted_at is not None:
            raise ValueError("User already deleted")
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(UserDeletedEvent.now(user_id=self._id, now=CreatedAt.from_datetime(now.value)))

    def enable(self) -> None:
        if self._status != UserStatus.DISABLED:
            raise ValueError(f"Cannot enable user in status {self._status!r}")
        self._status = UserStatus.ACTIVE

    def disable(self) -> None:
        if self._status != UserStatus.ACTIVE:
            raise ValueError(f"Cannot disable user in status {self._status!r}")
        self._status = UserStatus.DISABLED


from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.domain.user.aggregates.user.events.user_deleted_event import UserDeletedEvent
from shell.domain.user.aggregates.user.events.user_updated_event import UserUpdatedEvent
from shell.domain.user.value_objects.user_id import UserId
from shell.domain.user.value_objects.user_status import UserStatus

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.user.value_objects.user_email import UserEmail


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

    def update(self, email: UserEmail, now: datetime) -> None:
        self._email = email
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

    def disable(self, now: datetime) -> None:
        if self._status != UserStatus.ACTIVE:
            raise ValueError(f"Cannot disable user in status {self._status!r}")
        self._status = UserStatus.DISABLED


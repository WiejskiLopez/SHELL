"""SQL ORM model <-> domain entity mappers for User aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user.user import User
from shell.domain.user.value_objects.user_email import UserEmail
from shell.domain.user.value_objects.user_id import UserId
from shell.domain.user.value_objects.user_status import UserStatus
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)

if TYPE_CHECKING:
    from shell.infrastructure.user.user.persistence.sql.models.user import UserModel


def user_model_to_entity(model: UserModel) -> User:
    return User.restore(
        id=UserId(model.id),
        email=UserEmail(model.email),
        status=UserStatus(model.status),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
        updated_at=UpdatedAt.from_datetime(_ensure_utc(model.updated_at))
        if model.updated_at is not None
        else None,
        deleted_at=DeletedAt.from_datetime(_ensure_utc(model.deleted_at))
        if model.deleted_at is not None
        else None,
    )

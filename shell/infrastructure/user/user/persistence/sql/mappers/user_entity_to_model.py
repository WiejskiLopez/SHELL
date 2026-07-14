"""SQL ORM model <-> domain entity mappers for User aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.user.aggregates.user.user import User
from shell.domain.user.value_objects.user_email import UserEmail
from shell.domain.user.value_objects.user_id import UserId
from shell.domain.user.value_objects.user_status import UserStatus
from shell.infrastructure.user.user.persistence.sql.models.user import UserModel
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt


def user_entity_to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id.value,
        email=entity.email.value,
        status=entity.status.value,
        created_at=entity.created_at.value if entity.created_at else None,
        updated_at=entity.updated_at.value if entity.updated_at else None,
        deleted_at=entity.deleted_at.value if entity.deleted_at else None,
    )


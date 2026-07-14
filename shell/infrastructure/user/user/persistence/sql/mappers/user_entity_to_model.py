"""SQL ORM model <-> domain entity mappers for User aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.user.user.persistence.sql.models.user import UserModel

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user.user import User


def user_entity_to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id.value,
        email=entity.email.value,
        status=entity.status.value,
        created_at=entity.created_at.value if entity.created_at else None,
        updated_at=entity.updated_at.value if entity.updated_at else None,
        deleted_at=entity.deleted_at.value if entity.deleted_at else None,
    )


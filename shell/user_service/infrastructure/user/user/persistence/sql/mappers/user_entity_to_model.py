"""SQL ORM model <-> domain entity mappers for User aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.user_service.infrastructure.user.user.persistence.sql.models.user import UserModel

if TYPE_CHECKING:
    from shell.user_service.domain.user.aggregates.user.user import User


def user_entity_to_model(entity: User) -> UserModel:
    return UserModel(
        id=entity.id.value,
        email=entity.email.value,
        status=entity.status.value,
        created_at=entity.created_at.value if entity.created_at else None,
        changed_at=entity.changed_at.value,
        deleted_at=entity.deleted_at.value,
    )

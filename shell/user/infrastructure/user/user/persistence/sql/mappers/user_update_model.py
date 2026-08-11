"""SQL ORM model <-> domain entity mappers for User aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.user.domain.user.aggregates.user.user import User
    from shell.user.infrastructure.user.user.persistence.sql.models.user import UserModel


def user_update_model(model: UserModel, entity: User) -> None:
    model.email = entity.email.value
    model.status = entity.status.value
    assert entity.created_at is not None
    model.created_at = entity.created_at.value
    model.updated_at = entity.updated_at.value  # type: ignore[assignment]
    model.deleted_at = entity.deleted_at.value

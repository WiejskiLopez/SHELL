from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.user.aggregates.auth_session.auth_session import AuthSession
    from shell.infrastructure.user.auth_session.persistence.sql.models.auth_session import (
        AuthSessionModel,
    )


def auth_session_update_model(model: AuthSessionModel, entity: AuthSession) -> None:
    model.user_id = entity.user_id.value
    model.token_hash = entity.token_hash.value
    model.created_at = entity.created_at.value
    model.expires_at = entity.expires_at.value
    model.revoked_at = entity.revoked_at.value
    model.updated_at = entity.updated_at.value
    model.deleted_at = entity.deleted_at.value

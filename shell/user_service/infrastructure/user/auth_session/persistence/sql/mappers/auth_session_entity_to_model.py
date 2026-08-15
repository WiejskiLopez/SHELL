"""SQL ORM model <-> domain entity mappers for AuthSession aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.user_service.infrastructure.user.auth_session.persistence.sql.models.auth_session import (
    AuthSessionModel,
)

if TYPE_CHECKING:
    from shell.user_service.domain.user.aggregates.auth_session.auth_session import AuthSession


def auth_session_entity_to_model(auth_session: AuthSession) -> AuthSessionModel:
    return AuthSessionModel(
        id=auth_session.id.value,
        user_id=auth_session.user_id.value,
        token_hash=auth_session.token_hash.value,
        created_at=auth_session.created_at.value,
        expires_at=auth_session.expires_at.value,
        revoked_at=auth_session.revoked_at.value,
        updated_at=auth_session.updated_at.value,
        deleted_at=auth_session.deleted_at.value,
    )

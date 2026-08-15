"""SQL ORM model <-> domain entity mappers for AuthSession aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.hash import Hash
from shell.user_service.domain.user.aggregates.auth_session.auth_session import AuthSession
from shell.user_service.domain.user.aggregates.auth_session.value_objects.auth_session_id import (
    AuthSessionId,
)
from shell.user_service.domain.user.aggregates.auth_session.value_objects.expires_at import (
    ExpiresAt,
)
from shell.user_service.domain.user.aggregates.auth_session.value_objects.revoked_at import (
    RevokedAt,
)
from shell.user_service.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from shell.user_service.infrastructure.user.auth_session.persistence.sql.models.auth_session import (
        AuthSessionModel,
    )


def auth_session_model_to_entity(model: AuthSessionModel) -> AuthSession:
    return AuthSession.restore(
        id=AuthSessionId(model.id),
        user_id=UserId(model.user_id),
        token_hash=Hash(model.token_hash),
        created_at=CreatedAt.from_datetime(model.created_at),
        expires_at=ExpiresAt.from_datetime(model.expires_at),
        revoked_at=RevokedAt.from_datetime(model.revoked_at),
        changed_at=ChangedAt.from_datetime(model.changed_at),
        deleted_at=DeletedAt.from_datetime(model.deleted_at),
    )

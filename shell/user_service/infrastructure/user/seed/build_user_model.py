from __future__ import annotations

from datetime import UTC, datetime

from shell.user_service.infrastructure.user.user.persistence.sql.models.user import UserModel


def build_user_model(
    *,
    user_id: str,
    email: str,
    status: str,
    created_at: datetime | None = None,
) -> UserModel:
    """Build a UserModel with deterministic values."""
    return UserModel(
        id=user_id,
        email=email,
        status=status,
        created_at=created_at or datetime.now(tz=UTC),
    )

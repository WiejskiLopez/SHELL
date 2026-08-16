"""Builders producing User BC ORM model instances for seeding and tests."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.user_service.infrastructure.user.user.persistence.sql.models.user import UserModel
from shell.user_service.infrastructure.user.user_skill.persistence.sql.models.user_skill import (
    UserSkillModel,
)
from shell.user_service.infrastructure.user.user_state.persistence.sql.models.user_state import (
    UserStateModel,
)


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


def build_user_state_model(
    *,
    state_id: str,
    user_id: str,
    direction: str,
    state_data: dict[str, object],
    created_at: datetime | None = None,
) -> UserStateModel:
    """Build a UserStateModel with deterministic values."""
    return UserStateModel(
        id=state_id,
        user_id=user_id,
        direction=direction,
        state_data=state_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_user_skill_model(
    *,
    skill_id: str,
    user_id: str,
    skill_data: dict[str, object],
    created_at: datetime | None = None,
) -> UserSkillModel:
    """Build a UserSkillModel with deterministic values."""
    return UserSkillModel(
        id=skill_id,
        user_id=user_id,
        skill_data=skill_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


__all__ = [
    "build_user_model",
    "build_user_skill_model",
    "build_user_state_model",
]

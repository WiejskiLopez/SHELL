from __future__ import annotations

from datetime import UTC, datetime

from shell.user_service.infrastructure.user.user_skill.persistence.sql.models.user_skill import (
    UserSkillModel,
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

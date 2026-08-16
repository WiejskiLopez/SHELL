"""Builders producing Project BC ORM model instances for seeding and tests."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.project_service.infrastructure.project.project.persistence.sql.models.project import (
    ProjectModel,
)
from shell.project_service.infrastructure.project.project_skill.persistence.sql.models.project_skill import (
    ProjectSkillModel,
)
from shell.project_service.infrastructure.project.project_state.persistence.sql.models.project_state import (
    ProjectStateModel,
)


def build_project_model(
    *,
    project_id: str,
    name: str,
    repo_url: str | None,
    status: str,
    created_at: datetime | None = None,
) -> ProjectModel:
    """Build a ProjectModel with deterministic values."""
    return ProjectModel(
        id=project_id,
        name=name,
        repo_url=repo_url,
        status=status,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_project_state_model(
    *,
    state_id: str,
    project_id: str,
    direction: str,
    state_data: dict[str, object],
    created_at: datetime | None = None,
) -> ProjectStateModel:
    """Build a ProjectStateModel with deterministic values."""
    return ProjectStateModel(
        id=state_id,
        project_id=project_id,
        direction=direction,
        state_data=state_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


def build_project_skill_model(
    *,
    skill_id: str,
    project_id: str,
    skill_data: dict[str, object],
    created_at: datetime | None = None,
) -> ProjectSkillModel:
    """Build a ProjectSkillModel with deterministic values."""
    return ProjectSkillModel(
        id=skill_id,
        project_id=project_id,
        skill_data=skill_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


__all__ = [
    "build_project_model",
    "build_project_skill_model",
    "build_project_state_model",
]

"""SQL ORM model <-> domain entity mappers for ProjectState aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.project.project_state.persistence.sql.models.project_state import (
    ProjectStateModel,
)

if TYPE_CHECKING:
    from shell.domain.project.aggregates.project_state.project_state import ProjectState


def project_state_entity_to_model(entity: ProjectState) -> ProjectStateModel:
    return ProjectStateModel(
        id=entity.id.value,
        project_id=entity.project_id.value,
        direction=entity.direction.value,
        state_data=entity.snapshot(),
        created_at=entity.created_at.value if entity.created_at else None,
        updated_at=entity.updated_at.value,
        deleted_at=entity.deleted_at.value,
    )

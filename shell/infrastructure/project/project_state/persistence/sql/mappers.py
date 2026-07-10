"""SQL ORM model <-> domain entity mappers for ProjectState aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
from shell.domain.project.aggregates.project_state.project_state import ProjectState
from shell.domain.project.aggregates.project_state.value_objects.project_state_id import (
    ProjectStateId,
)
from shell.infrastructure.project.project_state.persistence.sql.models.project_state import (
    ProjectStateModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.domain.value_objects.updated_at import UpdatedAt


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def project_state_model_to_entity(model: ProjectStateModel) -> ProjectState:
    return ProjectState.restore(
        id=ProjectStateId(model.id),
        project_id=ProjectId(model.project_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at))
        if model.created_at
        else None,
        updated_at=UpdatedAt.from_datetime(_ensure_utc(model.updated_at))
        if model.updated_at is not None
        else None,
        deleted_at=DeletedAt.from_datetime(_ensure_utc(model.deleted_at))
        if model.deleted_at is not None
        else None,
    )


def project_state_entity_to_model(entity: ProjectState) -> ProjectStateModel:
    return ProjectStateModel(
        id=entity.id.value,
        project_id=entity.project_id.value,
        direction=entity.direction.value,
        state_data=entity.snapshot(),
        created_at=entity.created_at.value if entity.created_at else None,
        updated_at=entity.updated_at.value if entity.updated_at else None,
        deleted_at=entity.deleted_at.value if entity.deleted_at else None,
    )

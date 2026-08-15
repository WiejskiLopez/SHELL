"""SQL ORM model <-> domain entity mappers for ProjectState aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime
from shell.project_service.domain.project.aggregates.project.value_objects.project_id import (
    ProjectId,
)
from shell.project_service.domain.project.aggregates.project_state.project_state import ProjectState
from shell.project_service.domain.project.aggregates.project_state.value_objects.project_state_id import (
    ProjectStateId,
)

if TYPE_CHECKING:
    from shell.project_service.infrastructure.project.project_state.persistence.sql.models.project_state import (
        ProjectStateModel,
    )


def project_state_model_to_entity(model: ProjectStateModel) -> ProjectState:
    return ProjectState.restore(
        id=ProjectStateId(model.id),
        project_id=ProjectId(model.project_id),
        direction=StateDirection(model.direction),
        state_data=StateData(JsonStr(json.dumps(dict(model.state_data))))
        if model.state_data
        else StateData(JsonStr("{}")),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
        changed_at=ChangedAt.from_datetime(_ensure_utc(model.changed_at)),
        deleted_at=DeletedAt.from_datetime(_ensure_utc(model.deleted_at)),
    )

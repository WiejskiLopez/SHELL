"""SQL ORM model <-> domain entity mappers for Workflow aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.workflow import Workflow
    from shell.execution_service.infrastructure.execution.workflow.persistence.sql.models import (
        WorkflowModel,
    )


def workflow_change_model(model: WorkflowModel, entity: Workflow) -> None:
    model.status = entity.status.value if hasattr(entity.status, "value") else entity.status
    model.session_id = entity.session_id.value
    model.project_id = entity.project_id.value
    model.created_at = entity.created_at.value

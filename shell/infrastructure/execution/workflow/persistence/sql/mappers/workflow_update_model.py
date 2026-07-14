"""SQL ORM model <-> domain entity mappers for Workflow aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.infrastructure.execution.workflow.persistence.sql.models import WorkflowModel


def workflow_update_model(model: WorkflowModel, entity: Workflow) -> None:
    model.status = entity.status.value if hasattr(entity.status, "value") else entity.status
    model.session_id = entity.session_id.value if entity.session_id else None
    model.created_at = entity.created_at.value

"""SQL ORM model <-> domain entity mappers for Workflow aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.infrastructure.execution.workflow.persistence.sql.models import WorkflowModel

from ._created_at_value import _created_at_value

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.workflow import Workflow


def workflow_entity_to_model(work_flow: Workflow) -> WorkflowModel:
    return WorkflowModel(
        id=work_flow.id.value,
        status=work_flow.status.value,
        session_id=work_flow.session_id.value,
        project_id=work_flow.project_id.value,
        created_at=work_flow.created_at.value,
        deleted_at=_created_at_value(work_flow.deleted_at),
    )

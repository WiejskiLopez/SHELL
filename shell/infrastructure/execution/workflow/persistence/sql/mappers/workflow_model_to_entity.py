"""SQL ORM model <-> domain entity mappers for Workflow aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow.value_objects.workflow_status import WorkflowStatus
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt

if TYPE_CHECKING:
    from shell.infrastructure.execution.workflow.persistence.sql.models import WorkflowModel


def workflow_model_to_entity(workflow_model: WorkflowModel) -> Workflow:
    return Workflow.restore(
        id=WorkflowId(workflow_model.id),
        status=WorkflowStatus(workflow_model.status),
        session_id=SessionIdRef(workflow_model.session_id) if workflow_model.session_id else None,
        created_at=CreatedAt.from_datetime(workflow_model.created_at),
        deleted_at=(
            DeletedAt.from_datetime(workflow_model.deleted_at)
            if workflow_model.deleted_at
            else None
        ),
    )

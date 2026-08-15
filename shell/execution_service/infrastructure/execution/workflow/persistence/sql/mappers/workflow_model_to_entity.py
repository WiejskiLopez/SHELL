"""SQL ORM model <-> domain entity mappers for Workflow aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.project_id_ref import (
    ProjectIdRef,
)
from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.execution_service.domain.execution.aggregates.workflow import Workflow
from shell.execution_service.domain.execution.aggregates.workflow.value_objects.workflow_id import (
    WorkflowId,
)
from shell.execution_service.domain.execution.aggregates.workflow.value_objects.workflow_status import (
    WorkflowStatus,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt

if TYPE_CHECKING:
    from shell.execution_service.infrastructure.execution.workflow.persistence.sql.models import (
        WorkflowModel,
    )


def workflow_model_to_entity(workflow_model: WorkflowModel) -> Workflow:
    return Workflow.restore(
        id=WorkflowId(workflow_model.id),
        status=WorkflowStatus(workflow_model.status),
        session_id=SessionIdRef(workflow_model.session_id),
        project_id=ProjectIdRef(workflow_model.project_id),
        created_at=CreatedAt.from_datetime(workflow_model.created_at),
        deleted_at=(DeletedAt.from_datetime(workflow_model.deleted_at)),
    )

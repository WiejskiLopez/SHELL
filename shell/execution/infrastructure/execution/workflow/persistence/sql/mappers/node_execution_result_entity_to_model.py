"""SQL ORM model <-> domain entity mappers for Workflow aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.infrastructure.execution.node_execution.persistence.sql.models import (
    NodeExecutionResultModel,
)

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.workflow.entities.node_execution_result import (
        NodeExecutionResult,
    )


def node_execution_result_entity_to_model(
    node_execution_result: NodeExecutionResult,
) -> NodeExecutionResultModel:
    return NodeExecutionResultModel(
        id=node_execution_result.id.value,
        node_execution_id=node_execution_result.node_execution_id.value,
        workflow_id=node_execution_result.workflow_id.value,
        status=node_execution_result.status.value,
        stdout=node_execution_result.stdout,
        stderr=node_execution_result.stderr,
        artifact_uri=node_execution_result.artifact_uri,
        created_at=node_execution_result.created_at,
    )

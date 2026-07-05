"""Domain entity → DTO mappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.dto.runner_config import RunnerConfigDto
from shell.application.execution.dto.node_execution_result import NodeExecutionResultDto
from shell.application.execution.dto.task_execution import TaskExecutionDto
from shell.application.execution.dto.task_execution_state import TaskExecutionStateDto
from shell.application.execution.dto.workflow import WorkflowDto
from shell.application.execution.dto.workflow_state import WorkflowStateDto

if TYPE_CHECKING:
    from shell.domain.definition.entities.runner_config import RunnerConfig
    from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
    from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
        TaskExecutionState,
    )
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.aggregates.workflow.entities.node_execution_result import (
        NodeExecutionResult,
    )
    from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState


def task_execution_to_dto(task_execution: TaskExecution) -> TaskExecutionDto:
    return TaskExecutionDto(
        id=task_execution.id.value,
        name=task_execution.name.value,
        created_at=task_execution.created_at.value if task_execution.created_at else None,
        work_dir=task_execution.work_dir.value,
        workflow_id=task_execution.workflow_id.value if task_execution.workflow_id else None,
    )


def workflow_to_dto(workflow: Workflow) -> WorkflowDto:
    return WorkflowDto(
        id=workflow.id.value,
        status=workflow.status.value,
        created_at=workflow.created_at.value,
    )


def node_result_to_dto(result: NodeExecutionResult) -> NodeExecutionResultDto:
    return NodeExecutionResultDto(
        id=result.id.value,
        node_execution_id=result.node_execution_id.value,
        workflow_id=result.workflow_id.value,
        status=result.status.value,
        stdout=result.stdout.value if result.stdout else None,
        stderr=result.stderr.value if result.stderr else None,
        artifact_uri=result.artifact_uri.value if result.artifact_uri else None,
        created_at=result.created_at.value,
    )


def runner_config_to_dto(config: RunnerConfig) -> RunnerConfigDto:
    return RunnerConfigDto(
        id=config.id.value,
        package_name=config.package_name.value,
        kind=config.kind.value,
        hash=config.hash.value,
        body=config.body.value.copy(),
        created_at=config.created_at.value,
    )


def task_execution_state_to_dto(
    entity: TaskExecutionState,
) -> TaskExecutionStateDto:
    return TaskExecutionStateDto(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        is_current=entity.is_current,
        created_at=entity.created_at.value,
    )


def workflow_state_to_dto(
    entity: WorkflowState,
) -> WorkflowStateDto:
    return WorkflowStateDto(
        id=entity.id.value,
        workflow_id=entity.workflow_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        is_current=True,
        created_at=entity.created_at.value,
    )

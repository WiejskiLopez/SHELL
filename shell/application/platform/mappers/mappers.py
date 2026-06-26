"""Domain entity → DTO mappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.platform.dto import (
    EnvelopeDto,
    GraphNodeExecutionResultDto,
    GraphNodeExecutionStateInputDto,
    GraphNodeExecutionStateOutputDto,
    RunnerConfigDto,
    TaskExecutionDto,
    TaskExecutionStateInputDto,
    TaskExecutionStateOutputDto,
    WorkflowDto,
)

if TYPE_CHECKING:
    from shell.domain.definition.entities.runner_config import RunnerConfig
    from shell.domain.execution.aggregates.envelope import Envelope
    from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_input import (
        GraphNodeExecutionStateInput,
    )
    from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_output import (
        GraphNodeExecutionStateOutput,
    )
    from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
    from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
        TaskExecutionState,
    )
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.aggregates.workflow.entities.graph_node_execution_result import (
        GraphNodeExecutionResult,
    )


def task_execution_to_dto(task_execution: TaskExecution) -> TaskExecutionDto:
    return TaskExecutionDto(
        id=task_execution.id.value,
        name=task_execution.name.value,
        created_at=task_execution.created_at,
        work_dir=task_execution.work_dir,
        workflow_id=task_execution.workflow_id.value if task_execution.workflow_id else None,
    )


def workflow_to_dto(workflow: Workflow) -> WorkflowDto:
    return WorkflowDto(
        id=workflow.id.value,
        status=workflow.status.value,
        created_at=workflow.created_at,
    )


def envelope_to_dto(envelope: Envelope) -> EnvelopeDto:
    return EnvelopeDto(
        id=envelope.id.value,
        workflow_id=envelope.workflow_id.value,
        sender_graph_node_execution_id=envelope.sender_graph_node_execution_id.value,
        receiver_graph_node_execution_id=envelope.receiver_graph_node_execution_id.value,
        source_role=envelope.source_role.value,
        target_role=envelope.target_role.value,
        status=envelope.status.value,
        stage=envelope.stage.value,
        step=envelope.step.value,
        payload=envelope.payload.value,
        created_at=envelope.created_at.value,
        updated_at=envelope.updated_at.value,
    )


def node_result_to_dto(result: GraphNodeExecutionResult) -> GraphNodeExecutionResultDto:
    return GraphNodeExecutionResultDto(
        id=result.id.value,
        graph_node_execution_id=result.graph_node_execution_id.value,
        workflow_id=result.workflow_id.value,
        status=result.status.value,
        stdout=result.stdout,
        stderr=result.stderr,
        artifact_uri=result.artifact_uri,
        created_at=result.created_at,
    )


def runner_config_to_dto(config: RunnerConfig) -> RunnerConfigDto:
    return RunnerConfigDto(
        id=config.id.value,
        package_name=config.package_name,
        kind=config.kind,
        hash=config.hash.value,
        body=config.body,
        created_at=config.created_at,
    )


def task_execution_input_payload_to_dto(
    entity: TaskExecutionState,
) -> TaskExecutionStateInputDto:
    return TaskExecutionStateInputDto(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )


def task_execution_output_payload_to_dto(
    entity: TaskExecutionState,
) -> TaskExecutionStateOutputDto:
    return TaskExecutionStateOutputDto(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )


def graph_node_execution_state_input_to_dto(
    entity: GraphNodeExecutionStateInput,
) -> GraphNodeExecutionStateInputDto:
    return GraphNodeExecutionStateInputDto(
        id=entity.id.value,
        graph_node_execution_id=entity.graph_node_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )


def graph_node_execution_state_output_to_dto(
    entity: GraphNodeExecutionStateOutput,
) -> GraphNodeExecutionStateOutputDto:
    return GraphNodeExecutionStateOutputDto(
        id=entity.id.value,
        graph_node_execution_id=entity.graph_node_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )

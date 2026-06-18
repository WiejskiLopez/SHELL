"""Domain entity → DTO mappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.dto.dto import (
    EnvelopeDto,
    GraphNodeExecutionResultDto,
    GraphNodeExecutionStateDto,
    PromptDto,
    RunnerConfigDto,
    TaskExecutionDto,
    TaskExecutionInputPayloadDto,
    TaskExecutionOutputPayloadDto,
    WorkflowDto,
)

if TYPE_CHECKING:
    from shell.domain.entities.envelope import Envelope
    from shell.domain.entities.graph_node_execution_result import GraphNodeExecutionResult
    from shell.domain.entities.prompt import Prompt
    from shell.domain.entities.runner_config import RunnerConfig
    from shell.domain.aggregates.task_execution import TaskExecution
    from shell.domain.aggregates.task_execution_input_payload import (
        TaskExecutionInputPayload,
    )
    from shell.domain.aggregates.task_execution_output_payload import (
        TaskExecutionOutputPayload,
    )
    from shell.domain.aggregates.workflow import Workflow


def task_execution_to_dto(task_execution: TaskExecution) -> TaskExecutionDto:
    return TaskExecutionDto(
        id=task_execution.id.value,
        name=task_execution.name.value,
        version=task_execution.version.value,
        hash=task_execution.hash.value,
        is_current=task_execution.is_current,
        created_at=task_execution.created_at,
        body=task_execution.body.value,
        graph_node_executions=[],
    )


def workflow_to_dto(workflow: Workflow) -> WorkflowDto:
    graph_node_execution_states = {
        state_id: GraphNodeExecutionStateDto(
            graph_node_execution_id=state.graph_node_execution_id.value,
            status=state.status.value,
            step=state.step,
            updated_at=state.updated_at,
        )
        for state_id, state in workflow.graph_node_execution_states.items()
    }
    return WorkflowDto(
        id=workflow.id.value,
        task_execution_id=workflow.task_execution_id.value,
        status=workflow.status.value,
        created_at=workflow.created_at,
        graph_node_execution_states=graph_node_execution_states,
    )


def envelope_to_dto(envelope: Envelope) -> EnvelopeDto:
    return EnvelopeDto(
        id=envelope.id.value,
        workflow_id=envelope.workflow_id.value,
        sender_graph_node_execution_id=envelope.sender_graph_node_execution_id.value,
        receiver_graph_node_execution_id=envelope.receiver_graph_node_execution_id.value,
        source_role=envelope.source_role,
        target_role=envelope.target_role,
        status=envelope.status.value,
        stage=envelope.stage.value,
        step=envelope.step,
        payload=envelope.payload,
        created_at=envelope.created_at,
        updated_at=envelope.updated_at,
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


def prompt_to_dto(prompt: Prompt) -> PromptDto:
    return PromptDto(
        id=prompt.id.value,
        name=prompt.name,
        version=prompt.version,
        hash=prompt.hash.value,
        body=prompt.body,
        is_current=prompt.is_current,
        created_at=prompt.created_at,
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
    entity: TaskExecutionInputPayload,
) -> TaskExecutionInputPayloadDto:
    return TaskExecutionInputPayloadDto(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )


def task_execution_output_payload_to_dto(
    entity: TaskExecutionOutputPayload,
) -> TaskExecutionOutputPayloadDto:
    return TaskExecutionOutputPayloadDto(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        payload=entity.payload,
        is_current=entity.is_current,
        created_at=entity.created_at,
    )

"""Domain entity → DTO mappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.dto.dto import (
    EnvelopeDto,
    NodeResultDto,
    NodeStateDto,
    PromptDto,
    RunnerConfigDto,
    TaskExecutionDto,
    WorkflowDto,
)

if TYPE_CHECKING:
    from shell.domain.entities.envelope import Envelope
    from shell.domain.entities.node_result import NodeResult
    from shell.domain.entities.prompt import Prompt
    from shell.domain.entities.runner_config import RunnerConfig
    from shell.domain.entities.task_execution import TaskExecution
    from shell.domain.entities.workflow import Workflow


def task_execution_to_dto(task_execution: TaskExecution) -> TaskExecutionDto:
    return TaskExecutionDto(
        id=task_execution.id.value,
        name=task_execution.name.value,
        version=task_execution.version.value,
        hash=task_execution.hash.value,
        is_current=task_execution.is_current,
        created_at=task_execution.created_at,
        body=task_execution.body.value,
        graph_nodes=[],
    )


def workflow_to_dto(workflow: Workflow) -> WorkflowDto:
    states = {
        k: NodeStateDto(
            node_id=v.node_id.value,
            status=v.status.value,
            step=v.step,
            updated_at=v.updated_at,
        )
        for k, v in workflow.node_states.items()
    }
    return WorkflowDto(
        id=workflow.id.value,
        task_execution_id=workflow.task_execution_id.value,
        status=workflow.status.value,
        created_at=workflow.created_at,
        node_states=states,
    )


def envelope_to_dto(envelope: Envelope) -> EnvelopeDto:
    return EnvelopeDto(
        id=envelope.id.value,
        workflow_id=envelope.workflow_id.value,
        sender_node_id=envelope.sender_node_id.value,
        receiver_node_id=envelope.receiver_node_id.value,
        source_role=envelope.source_role,
        target_role=envelope.target_role,
        status=envelope.status.value,
        stage=envelope.stage.value,
        step=envelope.step,
        payload=envelope.payload,
        created_at=envelope.created_at,
        updated_at=envelope.updated_at,
    )


def node_result_to_dto(result: NodeResult) -> NodeResultDto:
    return NodeResultDto(
        id=result.id.value,
        node_id=result.node_id.value,
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

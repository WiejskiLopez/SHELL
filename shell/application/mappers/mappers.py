"""Domain entity → DTO mappers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.dto.dto import (
    EnvelopeDto,
    NodeResultDto,
    NodeStateDto,
    PromptDto,
    RunnerConfigDto,
    TaskDto,
    WorkflowDto,
)

if TYPE_CHECKING:
    from shell.domain.entities.envelope import Envelope
    from shell.domain.entities.node_result import NodeResult
    from shell.domain.entities.prompt import Prompt
    from shell.domain.entities.runner_config import RunnerConfig
    from shell.domain.entities.task import Task
    from shell.domain.entities.workflow import Workflow


def task_to_dto(task: Task) -> TaskDto:
    return TaskDto(
        id=task.id.value,
        name=task.name.value,
        version=task.version.value,
        hash=task.hash.value,
        is_current=task.is_current,
        created_at=task.created_at,
        body=task.body.value,
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
        task_id=workflow.task_id.value,
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

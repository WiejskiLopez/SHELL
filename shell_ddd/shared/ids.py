"""Shared ID generators."""
from __future__ import annotations

import uuid

from shell_ddd.domain.value_objects.ids import (
    EnvelopeId,
    NodeResultId,
    PromptId,
    RunnerConfigId,
    TaskId,
    WorkflowId,
)


class UuidIdGenerator:
    """Generates real UUID-based IDs."""

    def new_task_id(self) -> TaskId:
        return TaskId(str(uuid.uuid4()))

    def new_workflow_id(self) -> WorkflowId:
        return WorkflowId(str(uuid.uuid4()))

    def new_envelope_id(self) -> EnvelopeId:
        return EnvelopeId(str(uuid.uuid4()))

    def new_prompt_id(self) -> PromptId:
        return PromptId(str(uuid.uuid4()))

    def new_node_result_id(self) -> NodeResultId:
        return NodeResultId(str(uuid.uuid4()))

    def new_runner_config_id(self) -> RunnerConfigId:
        return RunnerConfigId(str(uuid.uuid4()))

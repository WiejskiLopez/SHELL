"""Execution domain exceptions."""

from __future__ import annotations

from shell.domain.execution.exceptions.envelope_not_found import EnvelopeNotFound
from shell.domain.execution.exceptions.graph_definition_not_found import GraphDefinitionNotFound
from shell.domain.execution.exceptions.invalid_envelope_transition import InvalidEnvelopeTransition
from shell.domain.execution.exceptions.invalid_node_mode import InvalidNodeMode
from shell.domain.execution.exceptions.invalid_task_definition import InvalidTaskDefinition
from shell.domain.execution.exceptions.invalid_workflow_transition import InvalidWorkflowTransition
from shell.domain.execution.exceptions.max_step_exceeded import MaxStepExceeded
from shell.domain.execution.exceptions.node_not_found import NodeNotFound
from shell.domain.execution.exceptions.role_not_resolvable import RoleNotResolvable
from shell.domain.execution.exceptions.task_execution_not_found import TaskExecutionNotFound
from shell.domain.execution.exceptions.workflow_concurrently_modified import (
    WorkflowConcurrentlyModified,
)
from shell.domain.execution.exceptions.workflow_has_no_nodes import WorkflowHasNoNodes
from shell.domain.execution.exceptions.workflow_not_found import WorkflowNotFound

__all__ = [
    "EnvelopeNotFound",
    "GraphDefinitionNotFound",
    "InvalidEnvelopeTransition",
    "InvalidNodeMode",
    "InvalidTaskDefinition",
    "InvalidWorkflowTransition",
    "MaxStepExceeded",
    "NodeNotFound",
    "RoleNotResolvable",
    "TaskExecutionNotFound",
    "WorkflowConcurrentlyModified",
    "WorkflowHasNoNodes",
    "WorkflowNotFound",
]

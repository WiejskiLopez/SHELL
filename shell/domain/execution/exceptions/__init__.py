"""Execution domain exceptions."""

from __future__ import annotations

from shell.domain.execution.aggregates.graph_node_execution.exceptions.invalid_node_mode import (
    InvalidNodeMode,
)
from shell.domain.execution.aggregates.graph_node_execution.exceptions.max_step_exceeded import (
    MaxStepExceeded,
)
from shell.domain.execution.aggregates.graph_node_execution.exceptions.role_not_resolvable import (
    RoleNotResolvable,
)
from shell.domain.execution.aggregates.task_execution.exceptions.invalid_task_definition import (
    InvalidTaskDefinition,
)
from shell.domain.execution.aggregates.task_execution.exceptions.task_execution_not_found import (
    TaskExecutionNotFound,
)
from shell.domain.execution.aggregates.workflow.exceptions.invalid_workflow_transition import (
    InvalidWorkflowTransition,
)
from shell.domain.execution.aggregates.workflow.exceptions.workflow_has_no_nodes import (
    WorkflowHasNoNodes,
)
from shell.domain.execution.aggregates.workflow.exceptions.workflow_not_found import (
    WorkflowNotFound,
)
from shell.domain.execution.exceptions.graph_definition_not_found import GraphDefinitionNotFound
from shell.domain.execution.exceptions.node_not_found import NodeNotFound

__all__ = [
    "GraphDefinitionNotFound",
    "InvalidNodeMode",
    "InvalidTaskDefinition",
    "InvalidWorkflowTransition",
    "MaxStepExceeded",
    "NodeNotFound",
    "RoleNotResolvable",
    "TaskExecutionNotFound",
    "WorkflowHasNoNodes",
    "WorkflowNotFound",
]

from __future__ import annotations

import uuid

from shell.domain.definition.value_objects.ids import RunnerConfigId
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
    TaskExecutionId,
    TaskExecutionStateId,
    WorkflowId,
)
from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId


class UuidIdGenerator:
    def new_task_execution_id(self) -> TaskExecutionId:
        return TaskExecutionId(str(uuid.uuid4()))

    def new_workflow_id(self) -> WorkflowId:
        return WorkflowId(str(uuid.uuid4()))

    def new_message_id(self) -> MessageId:
        return MessageId(str(uuid.uuid4()))

    def new_graph_node_execution_result_id(self) -> GraphNodeExecutionResultId:
        return GraphNodeExecutionResultId(str(uuid.uuid4()))

    def new_runner_config_id(self) -> RunnerConfigId:
        return RunnerConfigId(str(uuid.uuid4()))

    def new_graph_execution_id(self) -> GraphExecutionId:
        return GraphExecutionId(str(uuid.uuid4()))

    def new_graph_node_execution_id(self) -> GraphNodeExecutionId:
        return GraphNodeExecutionId(str(uuid.uuid4()))

    def new_task_execution_state_id(self) -> TaskExecutionStateId:
        return TaskExecutionStateId(str(uuid.uuid4()))

    def new_workflow_state_id(self) -> WorkflowStateId:
        return WorkflowStateId(str(uuid.uuid4()))

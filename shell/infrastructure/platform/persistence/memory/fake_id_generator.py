from __future__ import annotations

from shell.domain.definition.value_objects.ids import (
    GraphDefinitionId,
    GraphNodeDefinitionId,
    RagChunkId,
    RagDocumentId,
    RunnerConfigId,
)
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
    SessionId,
    TaskExecutionId,
    TaskExecutionStateId,
    WorkflowId,
)
from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId


class FakeIdGenerator:
    def __init__(self) -> None:
        self._counter = 0

    def _next(self) -> str:
        self._counter += 1
        return f"00000000-0000-0000-0000-{self._counter:012d}"

    def new_task_execution_id(self) -> TaskExecutionId:
        return TaskExecutionId(self._next())

    def new_workflow_id(self) -> WorkflowId:
        return WorkflowId(self._next())

    def new_message_id(self) -> MessageId:
        return MessageId(self._next())

    def new_graph_node_execution_result_id(self) -> GraphNodeExecutionResultId:
        return GraphNodeExecutionResultId(self._next())

    def new_runner_config_id(self) -> RunnerConfigId:
        return RunnerConfigId(self._next())

    def new_rag_document_id(self) -> RagDocumentId:
        return RagDocumentId(self._next())

    def new_rag_chunk_id(self) -> RagChunkId:
        return RagChunkId(self._next())

    def new_session_id(self) -> SessionId:
        return SessionId(self._next())

    def new_graph_definition_id(self) -> GraphDefinitionId:
        return GraphDefinitionId(self._next())

    def new_graph_node_definition_id(self) -> GraphNodeDefinitionId:
        return GraphNodeDefinitionId(self._next())

    def new_graph_execution_id(self) -> GraphExecutionId:
        return GraphExecutionId(self._next())

    def new_graph_node_execution_id(self) -> GraphNodeExecutionId:
        return GraphNodeExecutionId(self._next())

    def new_task_execution_state_id(self) -> TaskExecutionStateId:
        return TaskExecutionStateId(self._next())

    def new_workflow_state_id(self) -> WorkflowStateId:
        return WorkflowStateId(self._next())

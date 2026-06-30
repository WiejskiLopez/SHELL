"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

import pytest

from shell.application.execution.command_handlers.task_execution_import_handler import (
    TaskExecutionImportHandler,
)
from shell.application.execution.command_handlers.workflow_start_handler import WorkflowStartHandler
from shell.application.execution.commands.task_execution_commands import ImportTaskExecutionCommand
from shell.application.execution.commands.workflow_commands import StartWorkflowCommand
from shell.application.execution.queries.workflow_get_by_id_query import WorkflowGetByIdQuery
from shell.application.execution.query_handlers.workflow_get_by_id_handler import (
    WorkflowGetByIdHandler,
)
from shell.domain.execution.events import WorkflowStartedEvent
from shell.domain.execution.exceptions import TaskExecutionNotFound
from shell.infrastructure.execution.persistence.memory.in_memory_graph_node_execution_repository import (
    InMemoryGraphNodeExecutionRepository,
)
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
    InMemoryGraphExecutionRepository,
    InMemoryQueryServices,
    InMemoryTaskExecutionRepository,
    InMemoryUnitOfWork,
)


class TestWorkflowStartHandler:
    async def _import_task_execution(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> str:
        h = TaskExecutionImportHandler(
            unit_of_work, clock, id_generator, task_execution_loader, FakeLogger()
        )
        task_execution_id = await h.handle(ImportTaskExecutionCommand("t.md", "my-task"))
        await self._attach_graph_execution(unit_of_work, "my-task")
        return task_execution_id

    @staticmethod
    async def _attach_graph_execution(
        unit_of_work: InMemoryUnitOfWork, task_execution_name: str
    ) -> None:
        from shell.domain.execution.aggregates.graph_execution import GraphExecution
        from shell.domain.execution.aggregates.graph_node_execution import GraphNodeExecution
        from shell.domain.execution.value_objects.graph_depth import GraphDepth
        from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId
        from shell.domain.execution.value_objects.max_subgraph_depth import MaxSubgraphDepth
        from shell.domain.execution.value_objects.node_order import NodeOrder
        from shell.domain.execution.value_objects.node_role import NodeRole
        from shell.domain.execution.value_objects.node_type import NodeType
        from shell.domain.execution.value_objects.remaining_retries import RemainingRetries
        from shell.domain.execution.value_objects.retry_delay_seconds import RetryDelaySeconds
        from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
        from shell.domain.execution.value_objects.timeout_seconds import TimeoutSeconds
        from shell.domain.platform.value_objects.mode import Mode

        task_execution = await unit_of_work.repository(
            InMemoryTaskExecutionRepository
        ).get_current_by_name(TaskExecutionName(task_execution_name))
        assert task_execution is not None
        graph_execution = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=task_execution.id,
            depth=GraphDepth(0),
            max_subgraph_depth=MaxSubgraphDepth(5),
        )
        node = GraphNodeExecution(
            id=GraphNodeExecutionId(f"{task_execution_name}-node-0"),
            position=NodeOrder(0),
            mode=Mode("agent"),
            role=NodeRole.AGENT,
            node_type=NodeType("agent"),
            remaining_retries=RemainingRetries(3),
            retry_delay_seconds=RetryDelaySeconds(5),
            timeout_seconds=TimeoutSeconds(60),
        )
        node._graph_execution_id = graph_execution.id
        await unit_of_work.repository(InMemoryGraphExecutionRepository).save(graph_execution)
        await unit_of_work.repository(InMemoryGraphNodeExecutionRepository).save(node)

    async def test_happy_path(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> None:
        task_execution_id = await self._import_task_execution(
            unit_of_work, clock, id_generator, task_execution_loader
        )
        handler = WorkflowStartHandler(unit_of_work, clock, id_generator)
        wf_id = await handler.handle(StartWorkflowCommand(task_execution_id))

        assert wf_id
        assert any(isinstance(e, WorkflowStartedEvent) for e in unit_of_work.committed_events)

    async def test_task_not_found_raises(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        handler = WorkflowStartHandler(unit_of_work, clock, id_generator)
        with pytest.raises(TaskExecutionNotFound):
            await handler.handle(StartWorkflowCommand("nonexistent"))

    async def test_workflow_persisted(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
        queries: InMemoryQueryServices,
    ) -> None:
        task_execution_id = await self._import_task_execution(
            unit_of_work, clock, id_generator, task_execution_loader
        )
        handler = WorkflowStartHandler(unit_of_work, clock, id_generator)
        wf_id = await handler.handle(StartWorkflowCommand(task_execution_id))

        q_handler = WorkflowGetByIdHandler(queries)
        dto = await q_handler.handle(WorkflowGetByIdQuery(wf_id))
        assert dto is not None
        assert dto.status == "active"

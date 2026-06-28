"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

import pytest
from shell.application.execution.command_handlers.task_execution_import_handler import (
    TaskExecutionImportHandler,
)
from shell.application.execution.command_handlers.workflow_start_handler import WorkflowStartHandler
from shell.application.platform.commands import (
    ImportTaskExecutionCommand,
    StartWorkflowCommand,
)
from shell.application.platform.queries.queries import WorkflowGetByIdQuery
from shell.application.platform.query_handlers import WorkflowGetByIdHandler
from shell.domain.execution.events import WorkflowStartedEvent
from shell.domain.execution.exceptions import TaskExecutionNotFound
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
    InMemoryQueryServices,
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
        h = TaskExecutionImportHandler(unit_of_work, clock, id_generator, task_execution_loader, FakeLogger())
        task_execution_id = await h.handle(ImportTaskExecutionCommand("t.md", "my-task"))
        await self._attach_graph_execution(unit_of_work, "my-task")
        return task_execution_id

    @staticmethod
    async def _attach_graph_execution(unit_of_work: InMemoryUnitOfWork, task_execution_name: str) -> None:
        from shell.domain.execution.aggregates.graph_execution import GraphExecution
        from shell.domain.execution.aggregates.graph_node_execution import GraphNodeExecution
        from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId
        from shell.domain.execution.value_objects.node_order import NodeOrder
        from shell.domain.execution.value_objects.node_type import NodeType
        from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
        from shell.domain.platform.value_objects.mode import Mode

        task_execution = await unit_of_work.task_execution_repository.get_current_by_name(
            TaskExecutionName(task_execution_name)
        )
        assert task_execution is not None
        graph_execution = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=task_execution.id,
        )
        node = GraphNodeExecution(
            id=GraphNodeExecutionId(f"{task_execution_name}-node-0"),
            position=NodeOrder(0),
            mode=Mode("agent"),
            role="agent",
            node_type=NodeType("agent"),
        )
        node._graph_execution_id = graph_execution.id
        await unit_of_work.graph_execution_repository.save(graph_execution)
        await unit_of_work.graph_node_execution_repository.save(node)

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

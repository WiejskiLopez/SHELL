"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

import pytest
from shell.application.execution.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.execution.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell.application.platform.commands.commands import (
    ImportTaskExecutionCommand,
    StartWorkflowCommand,
)
from shell.application.platform.queries.queries import GetWorkflowQuery
from shell.application.platform.query_handlers.query_handlers import GetWorkflowHandler
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


class TestStartWorkflowHandler:
    async def _import_task_execution(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> str:
        h = ImportTaskExecutionHandler(uow, clock, id_gen, task_execution_loader, FakeLogger())
        task_execution_id = await h.handle(ImportTaskExecutionCommand("t.md", "my-task"))
        await self._attach_graph_execution(uow, "my-task")
        return task_execution_id

    @staticmethod
    async def _attach_graph_execution(uow: InMemoryUnitOfWork, task_execution_name: str) -> None:
        from shell.domain.definition.value_objects.ids import GraphDefinitionId
        from shell.domain.execution.aggregates.graph_execution import GraphExecution
        from shell.domain.execution.aggregates.graph_node_execution import GraphNodeExecution
        from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId
        from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
        from shell.domain.platform.value_objects.mode import Mode

        task_execution = await uow.task_executions.get_current_by_name(
            TaskExecutionName(task_execution_name)
        )
        assert task_execution is not None
        graph_execution = GraphExecution(
            id=GraphExecutionId.generate(),
            task_execution_id=task_execution.id,
            graph_definition_id=GraphDefinitionId("tpl"),
            graph_node_executions=[
                GraphNodeExecution(
                    id=GraphNodeExecutionId(f"{task_execution_name}-node-0"),
                    position=0,
                    mode=Mode("agent"),
                    role="agent",
                    node_type="agent",
                )
            ],
        )
        await uow.graph_executions.save(graph_execution)

    async def test_happy_path(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
    ) -> None:
        task_execution_id = await self._import_task_execution(
            uow, clock, id_gen, task_execution_loader
        )
        handler = StartWorkflowHandler(uow, clock, id_gen)
        wf_id = await handler.handle(StartWorkflowCommand(task_execution_id))

        assert wf_id
        assert any(isinstance(e, WorkflowStartedEvent) for e in uow.committed_events)

    async def test_task_not_found_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        handler = StartWorkflowHandler(uow, clock, id_gen)
        with pytest.raises(TaskExecutionNotFound):
            await handler.handle(StartWorkflowCommand("nonexistent"))

    async def test_workflow_persisted(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        task_execution_loader: FakeTaskLoader,
        queries: InMemoryQueryServices,
    ) -> None:
        task_execution_id = await self._import_task_execution(
            uow, clock, id_gen, task_execution_loader
        )
        handler = StartWorkflowHandler(uow, clock, id_gen)
        wf_id = await handler.handle(StartWorkflowCommand(task_execution_id))

        q_handler = GetWorkflowHandler(queries)
        dto = await q_handler.handle(GetWorkflowQuery(wf_id))
        assert dto is not None
        assert dto.status == "running"

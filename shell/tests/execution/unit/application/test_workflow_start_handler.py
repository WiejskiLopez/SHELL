"""Unit tests for application command handlers (using InMemory adapters)."""

from __future__ import annotations

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
from shell.domain.execution.aggregates.graph_execution.graph_execution import GraphExecution
from shell.domain.execution.aggregates.node_execution.node_execution import NodeExecution
from shell.domain.execution.aggregates.node_link_execution.node_link_execution import (
    NodeLinkExecution,
)
from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
    NodeLinkExecutionId,
)
from shell.domain.execution.events import WorkflowStartedEvent
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.ids import GraphExecutionId, NodeExecutionId
from shell.domain.execution.value_objects.max_subgraph_depth import MaxSubgraphDepth
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.platform.value_objects.mode import Mode
from shell.infrastructure.execution.persistence.memory.in_memory_node_execution_repository import (
    InMemoryNodeExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_node_link_execution_repository import (
    InMemoryNodeLinkExecutionRepository,
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
        node = NodeExecution(
            id=NodeExecutionId(f"{task_execution_name}-node-0"),
            position=NodeOrder(0),
            mode=Mode("agent"),
            role=NodeRole.AGENT,
            node_type=NodeType("agent"),
        )
        link = NodeLinkExecution(
            id=NodeLinkExecutionId.generate(),
            graph_execution_id=graph_execution.id,
            node_execution_id=node.id,
        )
        await unit_of_work.repository(InMemoryGraphExecutionRepository).save(graph_execution)
        await unit_of_work.repository(InMemoryNodeExecutionRepository).save(node)
        await unit_of_work.repository(InMemoryNodeLinkExecutionRepository).save(link)

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

    async def test_task_not_found_skips(
        self,
        unit_of_work: InMemoryUnitOfWork,
        clock: FakeClock,
        id_generator: FakeIdGenerator,
    ) -> None:
        handler = WorkflowStartHandler(unit_of_work, clock, id_generator)
        wf_id = await handler.handle(StartWorkflowCommand("nonexistent"))
        assert wf_id  # Workflow created, TaskExecution attach deferred to event handler

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

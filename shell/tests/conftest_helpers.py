"""Shared test helpers extracted from conftest.

from shell.infrastructure.execution.persistence.memory.in_memory_edge_execution_repository import (
        InMemoryEdgeExecutionRepository,
    )
from shell.domain.execution.services.node_execution_navigator import (
        LinearNodeExecutionNavigator,
    )
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
        GraphExecutionRepository,
    )
from shell.application.execution.event_handlers.workflow_started_attach_task_execution_handler import (
        WorkflowStartedAttachTaskExecutionHandler,
    )
Provides pure test-domain helpers (no pytest fixtures) used across all test
modules in the shell test suite.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from shell.application.execution.command_handlers.workflow_run_tasker_handler import (
    WorkflowRunTaskerHandler,
)
from shell.application.execution.event_handlers.node_execution_completed_handler import (
    NodeExecutionCompletedHandler,
)
from shell.application.execution.event_handlers.node_execution_worker import (
    NodeExecutionWorker,
)
from shell.application.execution.event_handlers.workflow_started_attach_task_execution_handler import (
    WorkflowStartedAttachTaskExecutionHandler,
)
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.value_objects.max_subgraph_depth import (
    MaxSubgraphDepth,
)
from shell.domain.execution.aggregates.node_execution.events.node_execution_completed_event import (
    NodeExecutionCompletedEvent,
)
from shell.domain.execution.aggregates.node_execution.events.node_execution_failed_event import (
    NodeExecutionFailedEvent,
)
from shell.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.execution.aggregates.node_link_execution.node_link_execution import (
    NodeLinkExecution,
)
from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
    NodeLinkExecutionId,
)
from shell.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.value_objects.task_execution_name import (
    TaskExecutionName,
)
from shell.domain.execution.value_objects.task_name import TaskName
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.events.node_execution_requested_event import (
    NodeExecutionRequestedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_started_event import (
    WorkflowStartedEvent,
)
from shell.domain.execution.services.node_execution_navigator import (
    LinearNodeExecutionNavigator,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    NodeExecutionId,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.platform.base import AggregateRoot, Entity
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.mode import Mode
from shell.framework.platform.api.app import create_app
from shell.infrastructure.execution.persistence.memory.in_memory_node_execution_repository import (
    InMemoryNodeExecutionRepository,
)
from shell.infrastructure.execution.persistence.memory.in_memory_node_link_execution_repository import (
    InMemoryNodeLinkExecutionRepository,
)
from shell.infrastructure.platform.configuration.shell_config import ShellConfig
from shell.infrastructure.platform.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    FakeNodeExecutionProcessRunner,
    InMemoryGraphExecutionRepository,
    InMemoryTaskExecutionRepository,
    InMemoryUnitOfWork,
    InMemoryWorkflowRepository,
)

# ---------------------------------------------------------------------------
# Domain fixtures — Entity base test helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _SampleId:
    value: str


@dataclass(frozen=True, slots=True)
class _SampleEvent(DomainEvent):
    payload: str = ""


class _SampleEntity(Entity[_SampleId]):
    __slots__ = ("_label",)

    def __init__(self, id: _SampleId, label: str) -> None:
        super().__init__(id)
        self._label = label

    @property
    def label(self) -> str:
        return self._label

    def relabel(self, label: str) -> None:
        self._label = label


class _SampleAggregate(AggregateRoot[_SampleId]):
    __slots__ = ("_label",)

    def __init__(self, id: _SampleId, label: str) -> None:
        super().__init__(id)
        self._label = label

    @property
    def label(self) -> str:
        return self._label

    def do_something(self, payload: str) -> None:
        now = datetime.now(tz=UTC)
        self.append_event(_SampleEvent(occurred_at=CreatedAt.from_datetime(now), payload=payload))


# ---------------------------------------------------------------------------
# Workflow step machine test helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _new_workflow() -> Workflow:
    return Workflow.new(id_=WorkflowId.generate(), now=_NOW)


def _ctx() -> object | None:
    return None


# ---------------------------------------------------------------------------
# Navigator test helpers
# ---------------------------------------------------------------------------


def _node_execution(
    node_execution_id: str, position: int, mode: str = "agent"
) -> NodeExecution:
    return NodeExecution(
        id=NodeExecutionId(node_execution_id),
        position=NodeOrder(position),
        mode=Mode(mode),
        role=NodeRole(mode.upper()),
        node_type=NodeType(mode),
    )


def _graph_execution(*node_executions: NodeExecution) -> GraphExecution:
    ge = GraphExecution(
        id=GraphExecutionId.generate(),
        task_execution_id=TaskExecutionId.generate(),
        depth=GraphDepth(0),
        max_subgraph_depth=MaxSubgraphDepth(5),
    )
    return ge


# ---------------------------------------------------------------------------
# Application fixtures
# ---------------------------------------------------------------------------


def _task_imported() -> TaskExecutionCreatedEvent:
    return TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId.generate(),
        task_execution_name=TaskExecutionName("test-task"),
        now=CreatedAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
    )


def _workflow_started() -> WorkflowStartedEvent:
    return WorkflowStartedEvent.now(
        workflow_id=WorkflowId.generate(),
        task_execution_id=TaskExecutionId.generate(),
        now=CreatedAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
    )


class _Spy(logging.Handler):
    def __init__(self, records: list[logging.LogRecord]) -> None:
        super().__init__()
        self._records = records

    def emit(self, record: logging.LogRecord) -> None:
        self._records.append(record)


def _spy_logger(
    name: str, level: int = logging.INFO
) -> tuple[StdlibLogger, list[logging.LogRecord]]:
    records: list[logging.LogRecord] = []
    logger = StdlibLogger(name, level=level)
    logger._logger.addHandler(_Spy(records))
    return logger, records


# ---------------------------------------------------------------------------
# NodeExecutionWorker test helpers
# ---------------------------------------------------------------------------


def _build_graph_execution(
    unit_of_work: InMemoryUnitOfWork, task_execution_name: str, modes: list[str]
) -> tuple[TaskExecution, GraphExecution, list[NodeExecution]]:
    task_execution = TaskExecution(
        id=TaskExecutionId.generate(),
        name=TaskName(task_execution_name),
        created_at=CreatedAt.from_datetime(_NOW),
    )
    unit_of_work.repository(InMemoryTaskExecutionRepository)._store[task_execution.id.value] = (
        task_execution
    )

    node_executions = [
        NodeExecution(
            id=NodeExecutionId(f"{task_execution.id.value}-n{i}"),
            position=NodeOrder(i),
            mode=Mode(m),
            role=NodeRole(m.upper()),
            node_type=NodeType(m),
        )
        for i, m in enumerate(modes)
    ]
    graph_execution = GraphExecution(
        id=GraphExecutionId.generate(),
        task_execution_id=task_execution.id,
        depth=GraphDepth(0),
        max_subgraph_depth=MaxSubgraphDepth(5),
    )
    link_repo = unit_of_work.repository(InMemoryNodeLinkExecutionRepository)
    for node in node_executions:
        unit_of_work.repository(InMemoryNodeExecutionRepository)._store[node.id.value] = node
        link_id = NodeLinkExecutionId(f"{graph_execution.id.value}-{node.id.value}")
        link_repo._store[link_id.value] = NodeLinkExecution(
            id=link_id,
            graph_execution_id=graph_execution.id,
            node_execution_id=node.id,
        )
    unit_of_work.repository(InMemoryGraphExecutionRepository)._store[graph_execution.id.value] = (
        graph_execution
    )
    return task_execution, graph_execution, node_executions


async def _persist_running_workflow(
    unit_of_work: InMemoryUnitOfWork,
    task_execution_id: TaskExecutionId,
    first_node: NodeExecutionId,
) -> Workflow:
    wf = Workflow.new(id_=WorkflowId.generate(), now=_NOW)
    wf.start_at(now=_NOW)
    task_execution = await unit_of_work.repository(InMemoryTaskExecutionRepository).get_by_id(
        task_execution_id
    )
    if task_execution is not None:
        task_execution.execute_in_workflow(wf.id)
    async with unit_of_work:
        await unit_of_work.repository(InMemoryWorkflowRepository).save(wf)
        if task_execution is not None:
            await unit_of_work.repository(InMemoryTaskExecutionRepository).save(task_execution)
        await unit_of_work.commit()
    return wf


def _make_worker(
    unit_of_work: InMemoryUnitOfWork,
    runner: FakeNodeExecutionProcessRunner,
) -> NodeExecutionWorker:
    return NodeExecutionWorker(
        unit_of_work=unit_of_work,
        clock=FakeClock(_NOW),
        id_generator=FakeIdGenerator(),
        runner=runner,
        logger=FakeLogger(),
    )


def _make_result_handler(
    unit_of_work: InMemoryUnitOfWork,
) -> NodeExecutionCompletedHandler:
    return NodeExecutionCompletedHandler(
        unit_of_work=unit_of_work,
        clock=FakeClock(_NOW),
        id_generator=FakeIdGenerator(),
        logger=FakeLogger(),
    )


# ---------------------------------------------------------------------------
# E2E helpers
# ---------------------------------------------------------------------------


async def _make_app(tmp_path):
    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    core_container = await ApplicationFactory(ShellConfig(database_url=db_url)).build()
    return create_app(core_container)


def _db_url(tmp_path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"


# ---------------------------------------------------------------------------
# E2E CLI task helpers
# ---------------------------------------------------------------------------


def _make_task_with_graph_execution(unit_of_work, task_execution_name, modes, now):
    task_execution = TaskExecution(
        id=TaskExecutionId.generate(),
        name=TaskName(task_execution_name),
        created_at=CreatedAt.from_datetime(now),
    )
    unit_of_work.repository(InMemoryTaskExecutionRepository)._store[task_execution.id.value] = (
        task_execution
    )
    node_executions = [
        NodeExecution(
            id=NodeExecutionId(f"{task_execution.id.value}-n{i}"),
            position=NodeOrder(i),
            mode=Mode(m),
            role=NodeRole(m.upper()),
            node_type=NodeType(m),
        )
        for i, m in enumerate(modes)
    ]
    graph_execution = GraphExecution(
        id=GraphExecutionId.generate(),
        task_execution_id=task_execution.id,
        depth=GraphDepth(0),
        max_subgraph_depth=MaxSubgraphDepth(5),
    )
    link_repo = unit_of_work.repository(InMemoryNodeLinkExecutionRepository)
    for node in node_executions:
        unit_of_work.repository(InMemoryNodeExecutionRepository)._store[node.id.value] = node
        link_repo._store[
            NodeLinkExecutionId(f"{graph_execution.id.value}-{node.id.value}")
        ] = NodeLinkExecution(
            id=NodeLinkExecutionId(f"{graph_execution.id.value}-{node.id.value}"),
            graph_execution_id=graph_execution.id,
            node_execution_id=node.id,
        )
    unit_of_work.repository(InMemoryGraphExecutionRepository)._store[graph_execution.id.value] = (
        graph_execution
    )
    return task_execution, graph_execution


async def _run_tasker_full(unit_of_work, clock, id_generator, command, runner=None):
    logger = FakeLogger()
    if runner is None:
        runner = FakeNodeExecutionProcessRunner(stdout="ok", returncode=0)
    worker = NodeExecutionWorker(
        unit_of_work=unit_of_work,
        clock=clock,
        id_generator=id_generator,
        logger=logger,
        runner=runner,
    )
    result_handler = NodeExecutionCompletedHandler(
        unit_of_work=unit_of_work, clock=clock, id_generator=id_generator, logger=logger
    )
    attach_handler = WorkflowStartedAttachTaskExecutionHandler(
        unit_of_work=unit_of_work, logger=logger
    )
    bootstrap_handler = WorkflowRunTaskerHandler(
        unit_of_work=unit_of_work, clock=clock, id_generator=id_generator
    )
    all_events = []
    await bootstrap_handler.handle(command)
    all_events.extend(unit_of_work.committed_events)
    max_iterations = 100
    for _ in range(max_iterations):
        batch = list(unit_of_work.committed_events)
        if not batch:
            break
        has_work = False
        for event in batch:
            if isinstance(event, WorkflowStartedEvent):
                await attach_handler.handle(event)
                all_events.extend(unit_of_work.committed_events)
                has_work = True
                # After attaching workflow, request first node
                task_id = event.task_execution_id
                if task_id is not None:
                    ge_repo = unit_of_work.repository(GraphExecutionRepository)
                    ge = await ge_repo.get_by_task_execution_id(task_id)
                    if ge is not None:
                        node_repo = unit_of_work.repository(InMemoryNodeExecutionRepository)
                        nav = LinearNodeExecutionNavigator()
                        first_node = await nav.first_async(ge, node_repo)
                        if first_node is not None:
                            async with unit_of_work:
                                request_event = NodeExecutionRequestedEvent.now(
                                    workflow_id=event.workflow_id,
                                    node_execution_id=first_node.id,
                                    now=CreatedAt.from_datetime(_NOW),
                                )
                                unit_of_work.stage_events([request_event])
                            all_events.extend(unit_of_work.committed_events)
                            has_work = True
            elif isinstance(event, NodeExecutionRequestedEvent):
                await worker.handle(event)
                all_events.extend(unit_of_work.committed_events)
                has_work = True
            elif isinstance(
                event, (NodeExecutionCompletedEvent, NodeExecutionFailedEvent)
            ):
                await result_handler.handle(event)
                all_events.extend(unit_of_work.committed_events)
                has_work = True
        if not has_work:
            break
    return all_events

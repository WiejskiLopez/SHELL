from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pathlib

import pytest

from shell.application.command_handlers.run_tasker_workflow_handler import RunTaskerWorkflowHandler
from shell.application.commands.workflow_commands import RunTaskerWorkflowCommand
from shell.application.event_handlers.graph_node_execution_result_handler import (
    GraphNodeExecutionResultHandler,
)
from shell.application.event_handlers.graph_node_execution_worker import GraphNodeExecutionWorker
from shell.domain.aggregates.graph_execution import GraphExecution
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.aggregates.task_execution import TaskExecution
from shell.domain.events.events import (
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionFailedEvent,
    GraphNodeExecutionRequestedEvent,
)
from shell.domain.value_objects.hash import Hash
from shell.domain.value_objects.ids import (
    GraphDefinitionId,
    GraphExecutionId,
    GraphNodeExecutionId,
    TaskExecutionId,
)
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.task_execution_body import TaskExecutionBody
from shell.domain.value_objects.task_execution_name import TaskExecutionName
from shell.domain.value_objects.version import Version
from shell.infrastructure.persistence.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    FakeNodeProcessRunner,
    InMemoryQueryServices,
    InMemoryUnitOfWork,
)


def _make_task_with_graph_execution(
    uow: InMemoryUnitOfWork,
    task_execution_name: str,
    modes: list[str],
    now: datetime,
) -> tuple[TaskExecution, GraphExecution]:
    task_execution = TaskExecution(
        id=TaskExecutionId.generate(),
        name=TaskExecutionName(task_execution_name),
        version=Version.initial(),
        hash=Hash.of("x"),
        body=TaskExecutionBody("# Task Body"),
        is_current=True,
        created_at=now,
    )
    uow.task_executions._store[task_execution.id.value] = task_execution  # type: ignore[attr-defined]

    graph_node_executions = [
        GraphNodeExecution(
            id=GraphNodeExecutionId(f"{task_execution.id.value}-n{i}"),
            position=i,
            mode=Mode(m),
            role=m,
            node_type=m,
        )
        for i, m in enumerate(modes)
    ]

    graph_execution = GraphExecution(
        id=GraphExecutionId.generate(),
        task_execution_id=task_execution.id,
        graph_definition_id=GraphDefinitionId("tpl"),
        graph_node_executions=graph_node_executions,
    )
    uow.graph_executions._store[graph_execution.id.value] = graph_execution  # type: ignore[attr-defined]
    return task_execution, graph_execution


async def _run_tasker_full(
    uow: InMemoryUnitOfWork,
    clock: FakeClock,
    id_gen: FakeIdGenerator,
    cmd: RunTaskerWorkflowCommand,
    runner: FakeNodeProcessRunner | None = None,
) -> list[Any]:
    """Run the full workflow saga and return all emitted domain events."""
    logger = FakeLogger()
    if runner is None:
        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)

    worker = GraphNodeExecutionWorker(
        uow=uow, clock=clock, id_gen=id_gen, logger=logger, runner=runner,
    )
    result_handler = GraphNodeExecutionResultHandler(
        uow=uow, clock=clock, id_gen=id_gen, logger=logger,
    )
    bootstrap_handler = RunTaskerWorkflowHandler(uow=uow, clock=clock, id_gen=id_gen)

    all_events: list[Any] = []

    # Phase 1: Bootstrap (creates workflow + first GraphNodeExecutionRequestedEvent)
    await bootstrap_handler.handle(cmd)
    all_events.extend(uow.committed_events)

    # Phase 2: Pump loop — process events as they are emitted
    # after each handler call, InMemoryUnitOfWork.committed_events is replaced
    # with the events from the latest commit, so we track our own queue.
    max_iterations = 100
    for _ in range(max_iterations):
        # Reload the latest batch of committed events
        batch = list(uow.committed_events)
        if not batch:
            break

        has_work = False
        for event in batch:
            if isinstance(event, GraphNodeExecutionRequestedEvent):
                await worker.handle(event)
                all_events.extend(uow.committed_events)
                has_work = True
            elif isinstance(event, (GraphNodeExecutionCompletedEvent, GraphNodeExecutionFailedEvent)):
                await result_handler.handle(event)
                all_events.extend(uow.committed_events)
                has_work = True

        if not has_work:
            break

    return all_events


@pytest.fixture()
def uow() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock(datetime(2026, 6, 1, tzinfo=UTC))


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def queries(uow: InMemoryUnitOfWork) -> InMemoryQueryServices:
    return InMemoryQueryServices(uow)


def _db_url(tmp_path: pathlib.Path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"

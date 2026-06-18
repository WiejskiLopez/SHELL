from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pathlib

import pytest

from shell.application.command_handlers.run_tasker_workflow_handler import RunTaskerWorkflowHandler
from shell.application.commands.workflow_commands import RunTaskerWorkflowCommand
from shell.application.event_handlers.graph_node_execution_worker import GraphNodeExecutionWorker
from shell.domain.entities.graph_execution import GraphExecution
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.entities.task_execution import TaskExecution
from shell.domain.events.events import GraphNodeExecutionRequested
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
from shell.infrastructure.persistence.memory.memory import (
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
            node_dir=f"/fake/{m}-{i}",
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
    logger = FakeLogger()
    if runner is None:
        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)

    worker = GraphNodeExecutionWorker(
        uow=uow,
        clock=clock,
        id_gen=id_gen,
        logger=logger,
        runner=runner,
    )

    handler = RunTaskerWorkflowHandler(uow=uow, clock=clock, id_gen=id_gen)
    await handler.handle(cmd)

    processed_count = 0
    while processed_count < len(uow.committed_events):
        event = uow.committed_events[processed_count]
        processed_count += 1

        if isinstance(event, GraphNodeExecutionRequested):
            await worker.handle(event)

    return uow.committed_events


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

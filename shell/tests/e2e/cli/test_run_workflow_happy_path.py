from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest

from shell.application.command_handlers.run_tasker_workflow_handler import RunTaskerWorkflowHandler
from shell.application.commands.commands import RunTaskerWorkflowCommand
from shell.application.event_handlers.node_execution_worker import NodeExecutionWorker
from shell.application.queries.queries import GetWorkflowQuery
from shell.application.query_handlers.query_handlers import GetWorkflowHandler
from shell.domain.entities.graph import Graph
from shell.domain.entities.graph_node import GraphNode
from shell.domain.entities.task_execution import TaskExecution
from shell.domain.events.events import (
    NodeCompleted,
    NodeExecutionRequested,
    NodeFailed,
    WorkflowCompleted,
    WorkflowFailed,
)
from shell.domain.value_objects.hash import Hash
from shell.domain.value_objects.ids import GraphDefinitionId, GraphId, NodeId, TaskExecutionId
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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task_with_graph(
    uow: InMemoryUnitOfWork,
    task_execution_name: str,
    modes: list[str],
    now: datetime,
) -> tuple[TaskExecution, Graph]:
    """Helper do przygotowania zadania wraz z powiązanym grafem wykonawczym."""
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

    nodes = [
        GraphNode(
            id=NodeId(f"{task_execution.id.value}-n{i}"),
            position=i,
            node_dir=f"/fake/{m}-{i}",
            mode=Mode(m),
            role=m,
            node_type=m,
        )
        for i, m in enumerate(modes)
    ]

    graph = Graph(
        id=GraphId.generate(),
        task_execution_id=task_execution.id,
        graph_definition_id=GraphDefinitionId("tpl"),
        nodes=nodes,
    )
    uow.graphs._store[graph.id.value] = graph  # type: ignore[attr-defined]
    return task_execution, graph


async def _run_tasker_full(
    uow: InMemoryUnitOfWork,
    clock: FakeClock,
    id_gen: FakeIdGenerator,
    cmd: RunTaskerWorkflowCommand,
    runner: FakeNodeProcessRunner | None = None,
) -> list[Any]:
    """Zrefaktorowany symulator pętli outbox/event-loop.

    Zamiast przetwarzać kaskadowo zdarzenia wewnątrz jednej transakcji,
    pętla czyta zdarzenia zakommitowane sekwencyjnie krok po kroku.
    """
    logger = FakeLogger()
    if runner is None:
        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)

    worker = NodeExecutionWorker(
        uow=uow,
        clock=clock,
        id_gen=id_gen,
        logger=logger,
        runner=runner,
    )

    # 1. Inicjalizacja i uruchomienie pierwszego kroku workflow przez handler komendy
    handler = RunTaskerWorkflowHandler(uow=uow, clock=clock, id_gen=id_gen)
    await handler.handle(cmd)

    # 2. Pętla kolejki przetwarzającej (Event-Loop / Outbox consumer)
    # Odpytujemy tablicę committed_events indeks po indeksie, pozwalając na
    # bezpieczne dopisywanie nowych zdarzeń z kolejnych, atomowych commitów workera.
    processed_count = 0
    while processed_count < len(uow.committed_events):
        event = uow.committed_events[processed_count]
        processed_count += 1

        if isinstance(event, NodeExecutionRequested):
            await worker.handle(event)

    return uow.committed_events


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------


class TestRunTaskerWorkflowHappyPath:
    async def test_all_nodes_complete_successfully(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
        queries: InMemoryQueryServices,
    ) -> None:
        # Arrange
        task_execution, _ = _make_task_with_graph(uow, "happy-path-task", ["agent", "tool"], clock.now())

        # Poprawne przekazanie task_execution_id oraz work_dir zgodnie z Twoją sygnaturą
        cmd = RunTaskerWorkflowCommand(task_execution_id=task_execution.id.value, work_dir="/fake/work/dir")

        # Act
        events = await _run_tasker_full(uow, clock, id_gen, cmd)

        # Assert
        assert any(isinstance(e, NodeCompleted) for e in events)
        assert any(isinstance(e, WorkflowCompleted) for e in events)
        assert not any(isinstance(e, WorkflowFailed) for e in events)

        workflows = list(uow.workflows._store.values())  # type: ignore[attr-defined]
        assert len(workflows) == 1

        get_wf = GetWorkflowHandler(queries)
        dto = await get_wf.handle(GetWorkflowQuery(workflows[0].id.value))
        assert dto is not None
        assert dto.status == "done"

    async def test_single_node_workflow(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        # Arrange
        task_execution, _ = _make_task_with_graph(uow, "single-node-task", ["agent"], clock.now())
        cmd = RunTaskerWorkflowCommand(task_execution_id=task_execution.id.value, work_dir="/fake/work/dir")

        # Act
        events = await _run_tasker_full(uow, clock, id_gen, cmd)

        # Assert
        assert any(isinstance(e, WorkflowCompleted) for e in events)
        workflows = list(uow.workflows._store.values())  # type: ignore[attr-defined]
        assert workflows[0].status.value == "done"


class TestRunTaskerWorkflowPartialFailure:
    async def test_node_failure_stops_execution(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        # Arrange
        task_execution, _ = _make_task_with_graph(uow, "failing-task", ["agent", "tool"], clock.now())
        cmd = RunTaskerWorkflowCommand(task_execution_id=task_execution.id.value, work_dir="/fake/work/dir")
        failing_runner = FakeNodeProcessRunner(stdout="execution failed", returncode=1)

        # Act
        events = await _run_tasker_full(uow, clock, id_gen, cmd, runner=failing_runner)

        # Assert
        assert any(isinstance(e, NodeFailed) for e in events)
        assert any(isinstance(e, WorkflowFailed) for e in events)
        assert not any(isinstance(e, WorkflowCompleted) for e in events)

        workflows = list(uow.workflows._store.values())  # type: ignore[attr-defined]
        assert len(workflows) == 1
        assert workflows[0].status.value == "failed"


class TestRunTaskerWorkflowEdgeCases:
    async def test_run_workflow_with_nonexistent_task_raises(
        self,
        uow: InMemoryUnitOfWork,
        clock: FakeClock,
        id_gen: FakeIdGenerator,
    ) -> None:
        # Arrange
        from shell.domain.exceptions import TaskExecutionNotFound

        cmd = RunTaskerWorkflowCommand(task_execution_id="ghost-task-id", work_dir="/fake/dir")
        handler = RunTaskerWorkflowHandler(uow=uow, clock=clock, id_gen=id_gen)

        # Act & Assert
        with pytest.raises(TaskExecutionNotFound):
            await handler.handle(cmd)

        assert uow.committed_events == []

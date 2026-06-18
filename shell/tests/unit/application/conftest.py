from __future__ import annotations

import logging
from datetime import UTC, datetime

import pytest

from shell.application.event_handlers.graph_node_execution_worker import GraphNodeExecutionWorker
from shell.domain.aggregates.graph_execution import GraphExecution
from shell.domain.entities.graph_node_execution import GraphNodeExecution
from shell.domain.aggregates.task_execution import TaskExecution
from shell.domain.aggregates.workflow import Workflow
from shell.domain.events.events import TaskExecutionCreated, WorkflowStarted
from shell.domain.value_objects.hash import Hash
from shell.domain.value_objects.ids import (
    GraphDefinitionId,
    GraphExecutionId,
    GraphNodeExecutionId,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.task_execution_body import TaskExecutionBody
from shell.domain.value_objects.task_execution_name import TaskExecutionName
from shell.domain.value_objects.version import Version
from shell.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)
from shell.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeIdGenerator,
    FakeLogger,
    FakeNodeProcessRunner,
    FakeTaskLoader,
    InMemoryQueryServices,
    InMemoryUnitOfWork,
)


def _task_imported() -> TaskExecutionCreated:
    return TaskExecutionCreated.now(
        task_execution_id=TaskExecutionId.generate(),
        task_execution_name=TaskExecutionName("t1"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _workflow_started() -> WorkflowStarted:
    return WorkflowStarted.now(
        workflow_id=WorkflowId.generate(),
        task_execution_id=TaskExecutionId.generate(),
        now=datetime(2026, 1, 1, tzinfo=UTC),
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


@pytest.fixture()
def uow() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture()
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture()
def id_gen() -> FakeIdGenerator:
    return FakeIdGenerator()


@pytest.fixture()
def task_execution_loader() -> FakeTaskLoader:
    return FakeTaskLoader(md="# My Task")


@pytest.fixture()
def fake_logger() -> FakeLogger:
    return FakeLogger()


@pytest.fixture()
def queries(uow: InMemoryUnitOfWork) -> InMemoryQueryServices:
    return InMemoryQueryServices(uow)


# ---------------------------------------------------------------------------
# GraphNodeExecutionWorker test helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _build_graph_execution(
    uow: InMemoryUnitOfWork, task_execution_name: str, modes: list[str]
) -> tuple[TaskExecution, GraphExecution]:
    task_execution = TaskExecution(
        id=TaskExecutionId.generate(),
        name=TaskExecutionName(task_execution_name),
        version=Version.initial(),
        hash=Hash.of("x"),
        body=TaskExecutionBody("# Task"),
        is_current=True,
        created_at=_NOW,
    )
    uow.task_executions._store[task_execution.id.value] = task_execution

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
    uow.graph_executions._store[graph_execution.id.value] = graph_execution
    return task_execution, graph_execution


async def _persist_running_workflow(
    uow: InMemoryUnitOfWork, task_execution_id: TaskExecutionId, first_node: GraphNodeExecutionId
) -> Workflow:
    wf = Workflow.new(id_=WorkflowId.generate(), task_execution_id=task_execution_id, now=_NOW)
    wf.start_at(
        first_graph_node_execution_id=first_node,
        context=WorkflowExecutionContext(work_dir="/tmp", correlation_id="cid"),
        now=_NOW,
    )
    async with uow:
        await uow.workflows.save(wf)
        await uow.commit()
    return wf


def _make_worker(
    uow: InMemoryUnitOfWork,
    runner: FakeNodeProcessRunner,
) -> GraphNodeExecutionWorker:
    return GraphNodeExecutionWorker(
        uow=uow,
        clock=FakeClock(_NOW),
        id_gen=FakeIdGenerator(),
        runner=runner,
        logger=FakeLogger(),
    )

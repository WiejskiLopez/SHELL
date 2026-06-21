"""Root conftest for shell tests.

Provides fixtures for all three persistence backends:
- InMemory (always available)
- SQLite (always available)
- PostgreSQL (skipped unless POSTGRES_TEST_URL env var set)
- MongoDB (skipped unless MONGO_TEST_URL env var set)
"""

from __future__ import annotations

import logging
import os
import pathlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest  # noqa: F401 — used in type annotations and fixtures
from shell.application.execution.command_handlers.run_tasker_workflow_handler import (
    RunTaskerWorkflowHandler,
)
from shell.application.execution.event_handlers.graph_node_execution_completed_handler import (
    GraphNodeExecutionCompletedHandler,
)
from shell.application.execution.event_handlers.graph_node_execution_worker import (
    GraphNodeExecutionWorker,
)
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory
from shell.bootstrap.platform.database_config.database_bootstrap import bootstrap_database
from shell.domain.definition.value_objects.ids import GraphDefinitionId
from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.task_execution.task_execution import TaskExecution
from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.events import (
    GraphNodeExecutionCompletedEvent,
    GraphNodeExecutionFailedEvent,
    GraphNodeExecutionRequestedEvent,
    TaskExecutionCreatedEvent,
    WorkflowStartedEvent,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,
    GraphNodeExecutionId,
    TaskExecutionId,
    WorkflowId,
)
from shell.domain.execution.value_objects.task_execution_body import TaskExecutionBody
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.execution.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)
from shell.domain.platform.base import AggregateRoot, Entity
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.hash import Hash
from shell.domain.platform.value_objects.mode import Mode
from shell.domain.platform.value_objects.version import Version
from shell.infrastructure.platform.configuration.shell_config import ShellConfig
from shell.infrastructure.platform.logging.stdlib_logger import (
    StdlibLogger,
    correlation_id_var,
)
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.platform.persistence.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeGraphNodeExecutionProcessRunner,
    FakeIdGenerator,
    FakeLogger,
    FakeTaskLoader,
    InMemoryQueryServices,
    InMemoryUnitOfWork,
)
from shell.infrastructure.platform.persistence.sql import build_session_factory

if TYPE_CHECKING:
    import pathlib

    from sqlalchemy.ext.asyncio import async_sessionmaker

# ---------------------------------------------------------------------------
# Markers
# ---------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: integration tests requiring external services")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


# ---------------------------------------------------------------------------
# Backend availability flags
# ---------------------------------------------------------------------------

POSTGRES_URL = os.environ.get(
    "POSTGRES_TEST_URL",
    "postgresql+asyncpg://shell_test:shell_test@localhost:5433/shell_test",
)
MONGO_URL = os.environ.get("MONGO_TEST_URL", "mongodb://localhost:27018/?replicaSet=rs0")

_postgres_available = os.environ.get("POSTGRES_TEST_URL") is not None
_mongo_available = os.environ.get("MONGO_TEST_URL") is not None

# ---------------------------------------------------------------------------
# Skip helpers
# ---------------------------------------------------------------------------

skip_no_postgres = pytest.mark.skipif(
    not _postgres_available,
    reason="POSTGRES_TEST_URL not set — start docker-compose.test.yml to enable",
)

skip_no_mongo = pytest.mark.skipif(
    not _mongo_available,
    reason="MONGO_TEST_URL not set — start docker-compose.test.yml to enable",
)


# ---------------------------------------------------------------------------
# URL fixtures (for integration tests that need raw URLs)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def sqlite_test_url(tmp_path_factory: pytest.TempPathFactory) -> str:
    db_path = tmp_path_factory.mktemp("db") / "test.db"
    return f"sqlite+aiosqlite:///{db_path}"


@pytest.fixture(scope="session")
def postgres_test_url() -> str:
    return POSTGRES_URL


@pytest.fixture(scope="session")
def mongo_test_url() -> str:
    return MONGO_URL


@pytest.fixture(autouse=True)
def auto_correlation_id():
    """Automatycznie ustawia correlation_id dla każdego testu."""
    token = correlation_id_var.set(f"test-{uuid.uuid4()}")
    yield
    correlation_id_var.reset(token)


@pytest.fixture
def queries(uow: InMemoryUnitOfWork) -> InMemoryQueryServices:
    return InMemoryQueryServices(uow)


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
        self.append_event(_SampleEvent(occurred_at=now, payload=payload))


# ---------------------------------------------------------------------------
# Workflow step machine test helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _new_workflow() -> Workflow:
    return Workflow.new(id_=WorkflowId.generate(), now=_NOW)


def _ctx() -> WorkflowExecutionContext:
    return WorkflowExecutionContext(correlation_id="cid-1")


# ---------------------------------------------------------------------------
# Navigator test helpers
# ---------------------------------------------------------------------------


def _graph_node_execution(
    graph_node_execution_id: str, position: int, mode: str = "agent"
) -> GraphNodeExecution:
    return GraphNodeExecution(
        id=GraphNodeExecutionId(graph_node_execution_id),
        position=position,
        mode=Mode(mode),
        role=mode,
        node_type=mode,
    )


def _graph_execution(*graph_node_executions: GraphNodeExecution) -> GraphExecution:
    return GraphExecution(
        id=GraphExecutionId.generate(),
        task_execution_id=TaskExecutionId.generate(),
        graph_definition_id=GraphDefinitionId("tpl"),
        graph_node_executions=list(graph_node_executions),
    )


# ---------------------------------------------------------------------------
# Application fixtures
# ---------------------------------------------------------------------------


def _task_imported() -> TaskExecutionCreatedEvent:
    return TaskExecutionCreatedEvent.now(
        task_execution_id=TaskExecutionId.generate(),
        task_execution_name=TaskExecutionName("t1"),
        now=datetime(2026, 1, 1, tzinfo=UTC),
    )


def _workflow_started() -> WorkflowStartedEvent:
    return WorkflowStartedEvent.now(
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
    return FakeTaskLoader(md="# SQL Task")


@pytest.fixture()
def fake_logger() -> FakeLogger:
    return FakeLogger()


# ---------------------------------------------------------------------------
# GraphNodeExecutionWorker test helpers
# ---------------------------------------------------------------------------


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
    wf = Workflow.new(id_=WorkflowId.generate(), now=_NOW)
    for ge in list(uow.graph_executions._store.values()):
        if ge.task_execution_id == task_execution_id:
            ge._workflow_id = wf.id
    wf.start_at(
        first_graph_node_execution_id=first_node,
        context=WorkflowExecutionContext(correlation_id="cid"),
        now=_NOW,
    )
    async with uow:
        await uow.workflows.save(wf)
        await uow.commit()
    return wf


def _make_worker(
    uow: InMemoryUnitOfWork,
    runner: FakeGraphNodeExecutionProcessRunner,
) -> GraphNodeExecutionWorker:
    return GraphNodeExecutionWorker(
        uow=uow,
        clock=FakeClock(_NOW),
        id_gen=FakeIdGenerator(),
        runner=runner,
        logger=FakeLogger(),
    )


def _make_result_handler(
    uow: InMemoryUnitOfWork,
) -> GraphNodeExecutionCompletedHandler:
    return GraphNodeExecutionCompletedHandler(
        uow=uow,
        clock=FakeClock(_NOW),
        id_gen=FakeIdGenerator(),
        logger=FakeLogger(),
    )


# ---------------------------------------------------------------------------
# SQLite integration fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def session_factory(
    tmp_path_factory: pytest.TempPathFactory,
) -> async_sessionmaker:
    db = tmp_path_factory.mktemp("sqlite") / "test.db"
    url = f"sqlite+aiosqlite:///{db}"
    await bootstrap_database(ShellConfig(database_url=url))
    return build_session_factory(url)


@pytest.fixture()
def events() -> FakeEventPublisher:
    return FakeEventPublisher()


@pytest.fixture()
def sql_uow(
    session_factory: async_sessionmaker,
    events: FakeEventPublisher,
) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session_factory)


# ---------------------------------------------------------------------------
# PostgreSQL integration fixtures
# ---------------------------------------------------------------------------


def pytest_collection_modifyitems(config, items):
    if os.environ.get("PG_TEST_URL") is None:
        skip_pg = pytest.mark.skip(reason="PG_TEST_URL not set")
        for item in items:
            if "sql_postgres" in str(item.fspath):
                item.add_marker(skip_pg)


# ---------------------------------------------------------------------------
# E2E helpers
# ---------------------------------------------------------------------------


async def _make_app(tmp_path: pathlib.Path):
    from shell.framework.platform.api.app import create_app

    db_url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    core_container = await ApplicationFactory(ShellConfig(database_url=db_url)).build()
    return create_app(core_container)


def _db_url(tmp_path: pathlib.Path) -> str:
    return f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"


# ---------------------------------------------------------------------------
# E2E CLI task helpers
# ---------------------------------------------------------------------------


def _make_task_with_graph_execution(uow, task_execution_name, modes, now):
    task_execution = TaskExecution(
        id=TaskExecutionId.generate(),
        name=TaskExecutionName(task_execution_name),
        version=Version.initial(),
        hash=Hash.of("x"),
        body=TaskExecutionBody("# Task Body"),
        is_current=True,
        created_at=now,
    )
    uow.task_executions._store[task_execution.id.value] = task_execution
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
    uow.graph_executions._store[graph_execution.id.value] = graph_execution
    return task_execution, graph_execution


async def _run_tasker_full(uow, clock, id_gen, cmd, runner=None):
    logger = FakeLogger()
    if runner is None:
        runner = FakeGraphNodeExecutionProcessRunner(stdout="ok", returncode=0)
    worker = GraphNodeExecutionWorker(
        uow=uow, clock=clock, id_gen=id_gen, logger=logger, runner=runner
    )
    result_handler = GraphNodeExecutionCompletedHandler(
        uow=uow, clock=clock, id_gen=id_gen, logger=logger
    )
    bootstrap_handler = RunTaskerWorkflowHandler(uow=uow, clock=clock, id_gen=id_gen)
    all_events = []
    await bootstrap_handler.handle(cmd)
    all_events.extend(uow.committed_events)
    max_iterations = 100
    for _ in range(max_iterations):
        batch = list(uow.committed_events)
        if not batch:
            break
        has_work = False
        for event in batch:
            if isinstance(event, GraphNodeExecutionRequestedEvent):
                await worker.handle(event)
                all_events.extend(uow.committed_events)
                has_work = True
            elif isinstance(
                event, (GraphNodeExecutionCompletedEvent, GraphNodeExecutionFailedEvent)
            ):
                await result_handler.handle(event)
                all_events.extend(uow.committed_events)
                has_work = True
        if not has_work:
            break
    return all_events

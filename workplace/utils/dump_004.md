### tests/unit/application/test_logging_publishers.py
```
"""Unit tests — Faza 11 logging/observability publishers."""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from shell_ddd.domain.events.events import TaskCreated, WorkflowStarted
from shell_ddd.domain.value_objects.ids import TaskId, WorkflowId
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell_ddd.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell_ddd.infrastructure.logging.stdlib_logger import (
    JsonFormatter,
    StdlibLogger,
    get_correlation_id,
    set_correlation_id,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task_imported() -> TaskCreated:
    return TaskCreated.now(task_id=TaskId.generate(), task_name=TaskName("t1"), now=datetime(2026, 1, 1, tzinfo=UTC))


def _workflow_started() -> WorkflowStarted:
    return WorkflowStarted.now(workflow_id=WorkflowId.generate(), task_name="t1", now=datetime(2026, 1, 1, tzinfo=UTC))


# ---------------------------------------------------------------------------
# StdlibLogger
# ---------------------------------------------------------------------------


def _spy_logger(name: str, level: int = logging.INFO) -> tuple[StdlibLogger, list[logging.LogRecord]]:
    """Return (StdlibLogger, records_list) — records_list is populated on each emit."""
    records: list[logging.LogRecord] = []

    class _Spy(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = StdlibLogger(name, level=level)
    logger._logger.addHandler(_Spy())
    return logger, records


class TestStdlibLogger:
    def test_info_writes_to_logger(self) -> None:
        logger, records = _spy_logger("test_stdlib_info")
        logger.info("hello world")
        assert any("hello world" in r.getMessage() for r in records)

    def test_warning_level(self) -> None:
        logger, records = _spy_logger("test_stdlib_warn")
        logger.warning("watch out")
        assert any(r.levelno == logging.WARNING for r in records)

    def test_error_level(self) -> None:
        logger, records = _spy_logger("test_stdlib_err")
        logger.error("boom")
        assert any(r.levelno == logging.ERROR for r in records)

    def test_debug_level(self) -> None:
        logger, records = _spy_logger("test_stdlib_dbg", level=logging.DEBUG)
        logger.debug("trace")
        assert any(r.levelno == logging.DEBUG for r in records)


class TestJsonFormatter:
    def _make_record(self, msg: str, level: int = logging.INFO) -> logging.LogRecord:
        record = logging.LogRecord(
            name="test", level=level, pathname="", lineno=0, msg=msg, args=(), exc_info=None
        )
        return record

    def test_output_is_valid_json(self) -> None:
        fmt = JsonFormatter()
        record = self._make_record("test message")
        output = fmt.format(record)
        data = json.loads(output)
        assert data["msg"] == "test message"
        assert "ts" in data
        assert "level" in data

    def test_includes_correlation_id(self) -> None:
        set_correlation_id("req-42")
        fmt = JsonFormatter()
        record = self._make_record("msg")
        data = json.loads(fmt.format(record))
        assert data["correlation_id"] == "req-42"
        # cleanup
        set_correlation_id("")

    def test_correlation_id_default_empty(self) -> None:
        set_correlation_id("")
        fmt = JsonFormatter()
        record = self._make_record("msg")
        data = json.loads(fmt.format(record))
        assert data["correlation_id"] == ""


class TestCorrelationId:
    def test_set_and_get(self) -> None:
        set_correlation_id("abc-123")
        assert get_correlation_id() == "abc-123"
        set_correlation_id("")


# ---------------------------------------------------------------------------
# LoggingEventPublisher
# ---------------------------------------------------------------------------


class TestLoggingEventPublisher:
    async def test_logs_each_event(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)
        events = [_task_imported(), _workflow_started()]
        await pub.publish(events)
        assert spy.info.call_count == 2

    async def test_logs_event_type(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)
        event = _task_imported()
        await pub.publish([event])
        call_kwargs = spy.info.call_args
        assert call_kwargs.kwargs.get("event_type") == "TaskCreated"

    async def test_empty_events_no_log(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)
        await pub.publish([])
        spy.info.assert_not_called()


# ---------------------------------------------------------------------------
# CompositeEventPublisher
# ---------------------------------------------------------------------------


class TestCompositeEventPublisher:
    async def test_fans_out_to_all_publishers(self) -> None:
        p1 = AsyncMock()
        p2 = AsyncMock()
        p3 = AsyncMock()
        composite = CompositeEventPublisher([p1, p2, p3])
        events = [_task_imported()]
        await composite.publish(events)
        p1.publish.assert_awaited_once_with(events)
        p2.publish.assert_awaited_once_with(events)
        p3.publish.assert_awaited_once_with(events)

    async def test_preserves_order(self) -> None:
        order: list[int] = []

        async def make_mock(n: int) -> object:
            class _Pub:
                async def publish(self, evs: list) -> None:
                    order.append(n)

            return _Pub()

        p1 = await make_mock(1)
        p2 = await make_mock(2)
        composite = CompositeEventPublisher([p1, p2])  # type: ignore[list-item]
        await composite.publish([_task_imported()])
        assert order == [1, 2]

    async def test_empty_publisher_list(self) -> None:
        composite = CompositeEventPublisher([])
        # should not raise
        await composite.publish([_task_imported()])
```

### tests/unit/application/test_node_execution_worker.py
```
"""Unit tests for ``NodeExecutionWorker`` (Process Manager / Saga step).

The worker subscribes to ``NodeExecutionRequested`` and processes exactly one
node per invocation. These tests verify:

* Happy path — node succeeds, cursor advances, next ``NodeExecutionRequested`` emitted.
* Last-node success — workflow transitions to ``done``.
* Node failure under ``FailFastPolicy`` — workflow transitions to ``failed``.
* Stale-cursor idempotency — events for a node the cursor no longer points at are dropped.
* Terminal-status idempotency — events delivered after ``done``/``failed`` are dropped.
"""
from __future__ import annotations

from datetime import UTC, datetime

from shell_ddd.application.event_handlers.node_execution_worker import NodeExecutionWorker
from shell_ddd.domain.entities.graph import Graph
from shell_ddd.domain.entities.graph_node import GraphNode
from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.events.events import (
    NodeAdvanced,
    NodeCompleted,
    NodeExecutionRequested,
    NodeFailed,
    WorkflowCompleted,
    WorkflowFailed,
)
from shell_ddd.domain.value_objects.hash import Hash
from shell_ddd.domain.value_objects.ids import (
    GraphId,
    NodeId,
    TaskId,
    TemplateGraphId,
    WorkflowId,
)
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.status import Status
from shell_ddd.domain.value_objects.task_body import TaskBody
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.domain.value_objects.version import Version
from shell_ddd.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)
from shell_ddd.infrastructure.persistence.memory.memory import (
    FakeClock,
    FakeEventPublisher,
    FakeIdGenerator,
    FakeLogger,
    FakeNodeProcessRunner,
    InMemoryUnitOfWork,
)


_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _build_graph(uow: InMemoryUnitOfWork, task_name: str, modes: list[str]) -> tuple[Task, Graph]:
    task = Task(
        id=TaskId.generate(),
        name=TaskName(task_name),
        version=Version.initial(),
        hash=Hash.of("x"),
        body=TaskBody("# Task"),
        is_current=True,
        created_at=_NOW,
    )
    uow.tasks._store[task.id.value] = task

    nodes = [
        GraphNode(
            id=NodeId(f"{task_name}-n{i}"),
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
        task_id=task.id,
        template_graph_id=TemplateGraphId("tpl"),
        raw_dict={},
        nodes=nodes,
    )
    uow.graphs._store[graph.id.value] = graph
    return task, graph


async def _persist_running_workflow(
    uow: InMemoryUnitOfWork, task_name: str, first_node: NodeId
) -> Workflow:
    wf = Workflow.new(id_=WorkflowId.generate(), task_name=task_name, now=_NOW)
    wf.start_at(
        first_node_id=first_node,
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
    publisher: FakeEventPublisher,
) -> NodeExecutionWorker:
    return NodeExecutionWorker(
        uow=uow,
        clock=FakeClock(_NOW),
        id_gen=FakeIdGenerator(),
        runner=runner,
        event_publisher=publisher,
        logger=FakeLogger(),
    )


class TestNodeExecutionWorkerHappyPath:
    async def test_first_node_success_advances_to_second(self) -> None:
        uow = InMemoryUnitOfWork()
        task, graph = _build_graph(uow, "happy", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task.name.value, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(stdout="ok", returncode=0)
        publisher = FakeEventPublisher()
        worker = _make_worker(uow, runner, publisher)

        await worker.handle(
            NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW)
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert stored.cursor.current_node_id == graph.nodes[1].id

        types = [type(e) for e in publisher.published]
        assert NodeCompleted in types
        assert NodeAdvanced in types
        assert NodeExecutionRequested in types

    async def test_last_node_success_finishes_workflow(self) -> None:
        uow = InMemoryUnitOfWork()
        task, graph = _build_graph(uow, "single", ["agent"])
        wf = await _persist_running_workflow(uow, task.name.value, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(returncode=0)
        publisher = FakeEventPublisher()
        worker = _make_worker(uow, runner, publisher)

        await worker.handle(
            NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW)
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.done()
        assert stored.cursor.current_node_id is None

        types = [type(e) for e in publisher.published]
        assert WorkflowCompleted in types


class TestNodeExecutionWorkerFailure:
    async def test_node_failure_aborts_under_fail_fast_policy(self) -> None:
        uow = InMemoryUnitOfWork()
        task, graph = _build_graph(uow, "fail", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task.name.value, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(returncode=1, stderr="boom")
        publisher = FakeEventPublisher()
        worker = _make_worker(uow, runner, publisher)

        await worker.handle(
            NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW)
        )

        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.failed()
        assert stored.cursor.current_node_id is None

        types = [type(e) for e in publisher.published]
        assert NodeFailed in types
        assert WorkflowFailed in types
        # Crucially — no advance, no further work requested.
        assert NodeAdvanced not in types
        assert NodeExecutionRequested not in types


class TestNodeExecutionWorkerIdempotency:
    async def test_stale_cursor_event_is_dropped(self) -> None:
        uow = InMemoryUnitOfWork()
        task, graph = _build_graph(uow, "stale", ["agent", "tool"])
        wf = await _persist_running_workflow(uow, task.name.value, graph.nodes[0].id)

        runner = FakeNodeProcessRunner(returncode=0)
        publisher = FakeEventPublisher()
        worker = _make_worker(uow, runner, publisher)

        # Worker is asked to process node[1] but the cursor still points at node[0].
        await worker.handle(
            NodeExecutionRequested.now(wf.id, graph.nodes[1].id, now=_NOW)
        )

        # Workflow state must be unchanged.
        stored = await uow.workflows.get_by_id(wf.id)
        assert stored is not None
        assert stored.status == Status.running()
        assert stored.cursor.current_node_id == graph.nodes[0].id
        # Runner was not called (early return).
        assert runner.calls == []
        # No domain events were published.
        assert publisher.published == []

    async def test_terminal_workflow_ignores_event(self) -> None:
        uow = InMemoryUnitOfWork()
        task, graph = _build_graph(uow, "terminal", ["agent"])
        wf = await _persist_running_workflow(uow, task.name.value, graph.nodes[0].id)

        # Force the workflow into ``done`` state directly.
        wf.record_node_result(
            result_id=FakeIdGenerator().new_node_result_id(),
            node_id=graph.nodes[0].id,
            status=Status.done(),
            now=_NOW,
        )
        wf.finish(_NOW)
        async with uow:
            await uow.workflows.save(wf)
            await uow.commit()

        runner = FakeNodeProcessRunner(returncode=0)
        publisher = FakeEventPublisher()
        worker = _make_worker(uow, runner, publisher)

        await worker.handle(
            NodeExecutionRequested.now(wf.id, graph.nodes[0].id, now=_NOW)
        )

        # Worker should silently ignore the re-delivery.
        assert runner.calls == []
        assert publisher.published == []
```

### tests/unit/application/test_outbox.py
```
"""Unit tests — Faza 12 outbox pattern."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from shell_ddd.domain.events.events import TaskCreated, WorkflowStarted
from shell_ddd.domain.value_objects.ids import TaskId, WorkflowId
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.messaging.memory_outbox_store import InMemoryOutboxStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task_imported() -> TaskCreated:
    return TaskCreated.now(task_id=TaskId.generate(), task_name=TaskName("t1"), now=datetime(2026, 1, 1, tzinfo=UTC))


def _workflow_started() -> WorkflowStarted:
    return WorkflowStarted.now(workflow_id=WorkflowId.generate(), task_name="t1", now=datetime(2026, 1, 1, tzinfo=UTC))


# ---------------------------------------------------------------------------
# InMemoryOutboxStore
# ---------------------------------------------------------------------------


class TestInMemoryOutboxStore:
    async def test_publish_adds_records(self) -> None:
        store = InMemoryOutboxStore()
        await store.publish([_task_imported(), _workflow_started()])
        assert len(store.records) == 2

    async def test_pending_returns_unpublished(self) -> None:
        store = InMemoryOutboxStore()
        await store.publish([_task_imported(), _task_imported()])
        assert len(store.pending()) == 2

    async def test_marking_published_removes_from_pending(self) -> None:
        from datetime import timezone

        store = InMemoryOutboxStore()
        await store.publish([_task_imported()])
        store.records[0].published_at = datetime.now(tz=UTC)
        assert store.pending() == []

    async def test_records_have_event_type(self) -> None:
        store = InMemoryOutboxStore()
        await store.publish([_task_imported()])
        assert store.records[0].event_type == "TaskCreated"

    async def test_empty_publish_no_records(self) -> None:
        store = InMemoryOutboxStore()
        await store.publish([])
        assert store.records == []
```

### tests/unit/domain/__init__.py
```
```

### tests/unit/domain/test_entities.py
```
"""Unit tests for domain entities."""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell_ddd.domain.entities.envelope import Envelope
from shell_ddd.domain.entities.task import Task
from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.exceptions import InvalidEnvelopeTransition
from shell_ddd.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell_ddd.domain.value_objects.ids import (
    EnvelopeId,
    NodeId,
    TaskId,
    WorkflowId, CorrelationId,
)
from shell_ddd.domain.value_objects.task_body import TaskBody
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.domain.value_objects.version import Version

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class TestTask:
    def test_create_yields_initial_task(self) -> None:
        task = Task.create(
            id_=TaskId.generate(),
            name=TaskName("my-task"),
            body=TaskBody("# Task"),
            now=_NOW,
        )
        assert task.is_current is True
        assert task.version == Version.initial()
        assert len(task.hash.value) == 64

    def test_create_emits_task_created_event(self) -> None:
        task = Task.create(
            id_=TaskId.generate(),
            name=TaskName("my-task"),
            body=TaskBody("# Task"),
            now=_NOW,
        )
        events = task.pull_events()
        assert len(events) == 1
        assert type(events[0]).__name__ == "TaskCreated"

    def test_hash_changes_with_content(self) -> None:
        t1 = Task.create(
            id_=TaskId.generate(),
            name=TaskName("t"),
            body=TaskBody("a"),
            now=_NOW,
        )
        t2 = Task.create(
            id_=TaskId.generate(),
            name=TaskName("t"),
            body=TaskBody("b"),
            now=_NOW,
        )
        assert t1.hash != t2.hash

    def test_supersede_marks_not_current(self) -> None:
        task = Task.create(
            id_=TaskId.generate(),
            name=TaskName("t"),
            body=TaskBody("a"),
            now=_NOW,
        )
        task.supersede()
        assert task.is_current is False


class TestWorkflow:
    def test_new_workflow_is_idle(self) -> None:
        wf = Workflow.new(id_=WorkflowId.generate(), task_name="my-task", now=_NOW)
        assert wf.status.value == "idle"

    def test_start_at_sets_running(self) -> None:
        from shell_ddd.domain.value_objects.workflow_execution_context import (
            WorkflowExecutionContext,
        )

        wf = Workflow.new(id_=WorkflowId.generate(), task_name="t", now=_NOW)
        wf.start_at(
            first_node_id=NodeId("n1"),
            context=WorkflowExecutionContext.empty(),
            now=_NOW,
        )
        assert wf.status.value == "running"
        assert wf.cursor.current_node_id == NodeId("n1")

    def test_update_node_state(self) -> None:
        from shell_ddd.domain.value_objects.status import Status

        wf = Workflow.new(id_=WorkflowId.generate(), task_name="t", now=_NOW)
        node_id = NodeId("node-1")
        wf.update_node_state(node_id, Status.running(), now=_NOW, step=2)
        assert wf.node_states["node-1"].step == 2


class TestEnvelope:
    def _make_envelope(self) -> Envelope:
        return Envelope.new(
            id_=EnvelopeId.generate(),
            workflow_id=WorkflowId.generate(),
            sender_node_id=NodeId("sender"),
            receiver_node_id=NodeId("receiver"),
            source_role="agent",
            target_role="router",
            now=_NOW,
        )

    def test_new_is_pending_draft(self) -> None:
        e = self._make_envelope()
        assert e.status == EnvelopeStatus.PENDING
        assert e.stage == EnvelopeStage.DRAFT

    def test_valid_transition_pending_to_active(self) -> None:
        e = self._make_envelope()
        e.transition_status(EnvelopeStatus.ACTIVE, now=_NOW)
        assert e.status == EnvelopeStatus.ACTIVE
        assert len(e.events) == 1

    def test_invalid_transition_raises(self) -> None:
        e = self._make_envelope()
        with pytest.raises(InvalidEnvelopeTransition):
            e.transition_status(EnvelopeStatus.DELIVERED, now=_NOW)  # PENDING → DELIVERED forbidden

    def test_dead_is_terminal(self) -> None:
        e = self._make_envelope()
        e.transition_status(EnvelopeStatus.DEAD, now=_NOW)
        with pytest.raises(InvalidEnvelopeTransition):
            e.transition_status(EnvelopeStatus.PENDING, now=_NOW)


# ---------------------------------------------------------------------------
# RagDocument / RagChunk
# ---------------------------------------------------------------------------


class TestRagDocument:
    from datetime import timezone

    _NOW = __import__("datetime").datetime(2025, 1, 1, tzinfo=__import__("datetime").timezone.utc)

    def _make_doc(self) -> "RagDocument":
        from shell_ddd.domain.entities.rag_document import RagDocument
        from shell_ddd.domain.value_objects.ids import RagDocumentId

        return RagDocument.new(
            id_=RagDocumentId.generate(),
            source_uri="file:///a.md",
            title="Test Doc",
            domain="test",
            now=self._NOW,
        )

    def test_new_creates_document_with_no_chunks(self) -> None:
        doc = self._make_doc()
        assert doc.chunks == []
        assert doc.source_uri == "file:///a.md"
        assert doc.domain == "test"

    def test_add_chunks_creates_correct_count(self) -> None:
        from shell_ddd.domain.value_objects.ids import RagChunkId

        doc = self._make_doc()
        ids = [RagChunkId.generate() for _ in range(3)]
        texts = ["chunk one", "chunk two", "chunk three"]
        embs = [b"\x00" * 4, b"\x00" * 4, b"\x00" * 4]
        doc.add_chunks(ids, texts, embs, "hash-stub")
        assert len(doc.chunks) == 3
        assert doc.chunks[0].chunk_index == 0
        assert doc.chunks[2].chunk_text == "chunk three"

    def test_add_chunks_mismatched_length_raises(self) -> None:
        from shell_ddd.domain.value_objects.ids import RagChunkId

        doc = self._make_doc()
        with pytest.raises(ValueError, match="equal length"):
            doc.add_chunks([RagChunkId.generate()], ["a", "b"], [b"\x00" * 4, b"\x00" * 4], "m")

    def test_empty_source_uri_raises(self) -> None:
        from shell_ddd.domain.entities.rag_document import RagDocument
        from shell_ddd.domain.value_objects.ids import RagDocumentId

        with pytest.raises(ValueError, match="source_uri"):
            RagDocument.new(id_=RagDocumentId.generate(), source_uri="", title="T", domain="d", now=self._NOW)

    def test_chunk_negative_index_raises(self) -> None:
        from shell_ddd.domain.entities.rag_document import RagChunk
        from shell_ddd.domain.value_objects.ids import RagChunkId, RagDocumentId

        doc_id = RagDocumentId.generate()
        with pytest.raises(ValueError, match="chunk_index"):
            RagChunk(
                id=RagChunkId.generate(),
                document_id=doc_id,
                chunk_index=-1,
                chunk_text="x",
                embedding=b"\x00" * 4,
                embedding_model="m",
            )


# ---------------------------------------------------------------------------
# Session / Message
# ---------------------------------------------------------------------------


class TestSession:
    _NOW = __import__("datetime").datetime(2025, 1, 1, tzinfo=__import__("datetime").timezone.utc)
    _LATER = __import__("datetime").datetime(2025, 1, 2, tzinfo=__import__("datetime").timezone.utc)

    def _make_session(self) -> "Session":
        from shell_ddd.domain.entities.session import Session
        from shell_ddd.domain.value_objects.ids import SessionId

        return Session.open(id_=SessionId.generate(), goal="do stuff", now=self._NOW)

    def test_open_creates_open_session(self) -> None:
        s = self._make_session()
        assert s.status == "open"
        assert s.closed_at is None
        assert s.messages == []

    def test_close_sets_status_and_closed_at(self) -> None:
        s = self._make_session()
        s.close(self._LATER)
        assert s.status == "closed"
        assert s.closed_at == self._LATER

    def test_close_twice_raises(self) -> None:
        s = self._make_session()
        s.close(self._LATER)
        with pytest.raises(ValueError, match="already closed"):
            s.close(self._LATER)

    def test_append_message(self) -> None:
        from shell_ddd.domain.value_objects.ids import MessageId

        s = self._make_session()
        msg = s.append_message(MessageId.generate(),CorrelationId.generate(), "agent-1", "router-1", {"text": "hi"}, self._NOW)
        assert msg.sender == "agent-1"
        assert len(s.messages) == 1

    def test_append_to_closed_session_raises(self) -> None:
        from shell_ddd.domain.value_objects.ids import MessageId

        s = self._make_session()
        s.close(self._LATER)
        with pytest.raises(ValueError, match="closed"):
            s.append_message(MessageId.generate(),CorrelationId.generate(), "a", "b", {}, self._NOW)

```

### tests/unit/domain/test_entity_base.py
```
"""Unit tests for Entity / AggregateRoot base classes."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell_ddd.domain.entities.base import AggregateRoot, Entity
from shell_ddd.domain.events.events import DomainEvent


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


class TestEntityIdentity:
    def test_id_is_exposed_via_property(self) -> None:
        e = _SampleEntity(_SampleId("a"), "x")
        assert e.id == _SampleId("a")

    def test_equality_is_identity_based(self) -> None:
        a1 = _SampleEntity(_SampleId("same"), "label-1")
        a2 = _SampleEntity(_SampleId("same"), "label-2-different")
        assert a1 == a2

    def test_inequality_for_different_ids(self) -> None:
        a = _SampleEntity(_SampleId("a"), "x")
        b = _SampleEntity(_SampleId("b"), "x")
        assert a != b

    def test_hash_matches_identity(self) -> None:
        a1 = _SampleEntity(_SampleId("same"), "label-1")
        a2 = _SampleEntity(_SampleId("same"), "label-2")
        assert hash(a1) == hash(a2)
        assert {a1, a2} == {a1}

    def test_compare_with_non_entity_returns_not_implemented(self) -> None:
        e = _SampleEntity(_SampleId("a"), "x")
        assert (e == "not-an-entity") is False


class TestAggregateEvents:
    def test_pull_events_returns_recorded_events(self) -> None:
        agg = _SampleAggregate(_SampleId("agg-1"), "x")
        agg.do_something("p1")
        agg.do_something("p2")

        events = agg.pull_events()
        assert len(events) == 2
        assert all(isinstance(e, _SampleEvent) for e in events)
        assert [e.payload for e in events] == ["p1", "p2"]  # type: ignore[attr-defined]

    def test_pull_events_clears_buffer(self) -> None:
        agg = _SampleAggregate(_SampleId("agg-2"), "x")
        agg.do_something("once")

        first = agg.pull_events()
        second = agg.pull_events()
        assert len(first) == 1
        assert second == []

    def test_pull_events_returns_copy_not_reference(self) -> None:
        agg = _SampleAggregate(_SampleId("agg-3"), "x")
        agg.do_something("only")

        first = agg.pull_events()
        agg.do_something("after-pull")

        # The first list captured is independent of the aggregate's buffer.
        assert len(first) == 1


class TestAggregateRootInheritance:
    def test_aggregate_is_an_entity(self) -> None:
        agg = _SampleAggregate(_SampleId("agg-x"), "x")
        assert isinstance(agg, Entity)

    def test_aggregate_event_buffer_is_per_instance(self) -> None:
        agg1 = _SampleAggregate(_SampleId("a"), "x")
        agg2 = _SampleAggregate(_SampleId("b"), "y")

        agg1.do_something("only-on-a")

        assert len(agg1.pull_events()) == 1
        assert agg2.pull_events() == []
```

### tests/unit/domain/test_node_execution_policy.py
```
"""Unit tests for ``NodeExecutionPolicy`` strategy.

The default ``FailFastPolicy`` always returns ``AbortDecision`` on failure,
preserving the legacy "any failure aborts the whole workflow" semantics.
The protocol allows future strategies (retry, continue-on-error, conditional
branching) to be plugged in without touching the ``NodeExecutionWorker``.
"""
from __future__ import annotations

from datetime import UTC, datetime

from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.services.node_execution_policy import (
    AbortDecision,
    ContinueDecision,
    FailFastPolicy,
)
from shell_ddd.domain.value_objects.ids import NodeId, WorkflowId


def _workflow() -> Workflow:
    return Workflow.new(
        id_=WorkflowId.generate(),
        task_name="x",
        now=datetime.now(tz=UTC),
    )


class TestFailFastPolicy:
    def test_decide_after_failure_returns_abort_decision(self) -> None:
        policy = FailFastPolicy()
        wf = _workflow()
        decision = policy.decide_after_failure(wf, NodeId("n1"), reason="boom")
        assert isinstance(decision, AbortDecision)
        assert decision.reason == "boom"

    def test_continue_decision_is_distinguishable_from_abort(self) -> None:
        cont = ContinueDecision()
        abort = AbortDecision(reason="x")
        # Type-level discrimination must be sound.
        assert isinstance(cont, ContinueDecision)
        assert isinstance(abort, AbortDecision)
        assert not isinstance(cont, AbortDecision)
        assert not isinstance(abort, ContinueDecision)
```

### tests/unit/domain/test_node_navigator.py
```
"""Unit tests for ``LinearNodeNavigator`` (and the ``NodeNavigator`` Protocol)."""
from __future__ import annotations

from shell_ddd.domain.entities.graph import Graph
from shell_ddd.domain.entities.graph_node import GraphNode
from shell_ddd.domain.services.node_navigator import LinearNodeNavigator
from shell_ddd.domain.value_objects.ids import GraphId, NodeId, TaskId, TemplateGraphId
from shell_ddd.domain.value_objects.mode import Mode


def _node(node_id: str, position: int, mode: str = "agent") -> GraphNode:
    return GraphNode(
        id=NodeId(node_id),
        position=position,
        node_dir=f"/fake/{node_id}",
        mode=Mode(mode),
        role=mode,
        node_type=mode,
    )


def _graph(*nodes: GraphNode) -> Graph:
    return Graph(
        id=GraphId.generate(),
        task_id=TaskId.generate(),
        template_graph_id=TemplateGraphId("tpl"),
        raw_dict={},
        nodes=list(nodes),
    )


class TestLinearNodeNavigatorFirst:
    def test_first_returns_lowest_position(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph(_node("b", 1), _node("a", 0), _node("c", 2))
        result = nav.first(graph)
        assert result is not None
        assert result.id == NodeId("a")

    def test_first_on_empty_graph_returns_none(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph()
        assert nav.first(graph) is None

    def test_first_handles_unsorted_input(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph(_node("z", 5), _node("y", 3), _node("x", 1))
        first = nav.first(graph)
        assert first is not None
        assert first.id == NodeId("x")


class TestLinearNodeNavigatorNextAfter:
    def test_next_after_returns_following_node(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph(_node("a", 0), _node("b", 1), _node("c", 2))
        nxt = list(nav.next_after(graph, NodeId("a")))
        assert len(nxt) == 1
        assert nxt[0].id == NodeId("b")

    def test_next_after_last_node_returns_empty(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph(_node("a", 0), _node("b", 1))
        assert list(nav.next_after(graph, NodeId("b"))) == []

    def test_next_after_unknown_node_returns_empty(self) -> None:
        nav = LinearNodeNavigator()
        graph = _graph(_node("a", 0))
        assert list(nav.next_after(graph, NodeId("ghost"))) == []

    def test_next_after_respects_position_ordering(self) -> None:
        nav = LinearNodeNavigator()
        # Out-of-order list, but ordering must follow ``position``.
        graph = _graph(_node("c", 2), _node("a", 0), _node("b", 1))
        nxt = list(nav.next_after(graph, NodeId("a")))
        assert nxt and nxt[0].id == NodeId("b")
        nxt2 = list(nav.next_after(graph, NodeId("b")))
        assert nxt2 and nxt2[0].id == NodeId("c")
```

### tests/unit/domain/test_smoke.py
```
"""Smoke test — verifies pytest can collect and run tests in shell_ddd."""


def test_smoke() -> None:
    assert True
```

### tests/unit/domain/test_value_objects.py
```
"""Unit tests for domain value objects."""
from __future__ import annotations

from datetime import UTC

import pytest

from shell_ddd.domain.value_objects.hash import Hash
from shell_ddd.domain.value_objects.ids import EnvelopeId, TaskId, WorkflowId
from shell_ddd.domain.value_objects.mode import Mode
from shell_ddd.domain.value_objects.status import Status
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.domain.value_objects.timestamp import Timestamp


class TestTaskName:
    def test_valid(self) -> None:
        tn = TaskName("my-task")
        assert str(tn) == "my-task"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskName("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskName("   ")

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskName("x" * 256)


class TestHash:
    def test_of_string(self) -> None:
        h = Hash.of("hello")
        assert len(h.value) == 64

    def test_deterministic(self) -> None:
        assert Hash.of("abc") == Hash.of("abc")

    def test_different_inputs(self) -> None:
        assert Hash.of("abc") != Hash.of("xyz")

    def test_invalid_length(self) -> None:
        with pytest.raises(ValueError):
            Hash("short")

    def test_invalid_hex(self) -> None:
        with pytest.raises(ValueError):
            Hash("z" * 64)


class TestIds:
    def test_task_id_generate(self) -> None:
        t1 = TaskId.generate()
        t2 = TaskId.generate()
        assert t1 != t2
        assert len(t1.value) == 36  # UUID4

    def test_task_id_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskId("")

    def test_workflow_id_generate(self) -> None:
        w = WorkflowId.generate()
        assert w.value

    def test_envelope_id_generate(self) -> None:
        e = EnvelopeId.generate()
        assert e.value


class TestMode:
    def test_values(self) -> None:
        assert Mode.AGENT.value == "agent"
        assert Mode.ROUTER.value == "router"

    def test_str_enum(self) -> None:
        assert Mode("worker") == Mode.WORKER


class TestStatus:
    def test_sentinels(self) -> None:
        assert Status.idle().value == "idle"
        assert Status.running().value == "running"
        assert Status.done().value == "done"
        assert Status.failed().value == "failed"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            Status("")


class TestTimestamp:
    def test_now_is_utc(self) -> None:

        ts = Timestamp.now()
        assert ts.value.tzinfo == UTC

    def test_naive_raises(self) -> None:
        from datetime import datetime

        with pytest.raises(ValueError):
            Timestamp(datetime(2024, 1, 1))  # naive
```

### tests/unit/domain/test_value_objects_task_body.py
```
"""Unit tests for TaskBody value object."""
from __future__ import annotations

import pytest

from shell_ddd.domain.value_objects.task_body import TaskBody


class TestTaskBody:
    def test_holds_text_value(self) -> None:
        b = TaskBody("# My Task\n\nSome content")
        assert b.value == "# My Task\n\nSome content"

    def test_str_returns_value(self) -> None:
        b = TaskBody("hello")
        assert str(b) == "hello"

    def test_equality(self) -> None:
        assert TaskBody("a") == TaskBody("a")
        assert TaskBody("a") != TaskBody("b")

    def test_is_hashable(self) -> None:
        s = {TaskBody("x"), TaskBody("x"), TaskBody("y")}
        assert s == {TaskBody("x"), TaskBody("y")}

    @pytest.mark.parametrize("invalid", ["", " ", "\n", "\t", "   \n  "])
    def test_empty_or_whitespace_rejected(self, invalid: str) -> None:
        with pytest.raises(ValueError, match="TaskBody cannot be empty"):
            TaskBody(invalid)

    def test_is_frozen(self) -> None:
        b = TaskBody("x")
        with pytest.raises((AttributeError, Exception)):
            b.value = "y"  # type: ignore[misc]
```

### tests/unit/domain/test_value_objects_version.py
```
"""Unit tests for Version value object."""
from __future__ import annotations

import pytest

from shell_ddd.domain.value_objects.version import Version


class TestVersion:
    def test_initial_returns_version_one(self) -> None:
        assert Version.initial() == Version(1)

    def test_next_increments_value(self) -> None:
        v = Version(3)
        assert v.next() == Version(4)

    def test_next_does_not_mutate_original(self) -> None:
        v = Version(2)
        v.next()
        assert v == Version(2)

    def test_str_representation(self) -> None:
        assert str(Version(7)) == "7"

    def test_equality(self) -> None:
        assert Version(5) == Version(5)
        assert Version(5) != Version(6)

    def test_is_hashable(self) -> None:
        s = {Version(1), Version(1), Version(2)}
        assert s == {Version(1), Version(2)}

    @pytest.mark.parametrize("invalid", [0, -1, -100])
    def test_value_below_one_is_rejected(self, invalid: int) -> None:
        with pytest.raises(ValueError, match="Version must be >= 1"):
            Version(invalid)

    def test_is_frozen(self) -> None:
        v = Version(1)
        with pytest.raises((AttributeError, Exception)):
            v.value = 99  # type: ignore[misc]
```

### tests/unit/domain/test_workflow_cursor.py
```
"""Unit tests for ``WorkflowCursor`` value object.

WorkflowCursor is the execution pointer that lets the worker know which node
should be processed next. The VO must be immutable, comparable by value, and
expose a small algebra (``empty``, ``at``, ``cleared``, ``points_to``,
``is_active``).
"""
from __future__ import annotations

import pytest

from shell_ddd.domain.value_objects.ids import NodeId
from shell_ddd.domain.value_objects.workflow_cursor import WorkflowCursor


class TestWorkflowCursorConstruction:
    def test_empty_factory_yields_inactive_cursor(self) -> None:
        cur = WorkflowCursor.empty()
        assert cur.current_node_id is None
        assert cur.is_active() is False

    def test_at_factory_points_to_node(self) -> None:
        node = NodeId("step-1")
        cur = WorkflowCursor.at(node)
        assert cur.current_node_id == node
        assert cur.is_active() is True

    def test_cursor_is_immutable(self) -> None:
        cur = WorkflowCursor.at(NodeId("x"))
        with pytest.raises(Exception):  # frozen dataclass → FrozenInstanceError
            cur.current_node_id = NodeId("y")  # type: ignore[misc]


class TestWorkflowCursorAlgebra:
    def test_points_to_matches_only_current_node(self) -> None:
        cur = WorkflowCursor.at(NodeId("alpha"))
        assert cur.points_to(NodeId("alpha")) is True
        assert cur.points_to(NodeId("beta")) is False

    def test_points_to_on_empty_cursor_is_always_false(self) -> None:
        cur = WorkflowCursor.empty()
        assert cur.points_to(NodeId("anything")) is False

    def test_cleared_returns_empty_cursor(self) -> None:
        cur = WorkflowCursor.at(NodeId("step-1")).cleared()
        assert cur == WorkflowCursor.empty()
        assert cur.is_active() is False

    def test_value_equality(self) -> None:
        a = WorkflowCursor.at(NodeId("n"))
        b = WorkflowCursor.at(NodeId("n"))
        c = WorkflowCursor.at(NodeId("m"))
        assert a == b
        assert a != c
```

### tests/unit/domain/test_workflow_step_machine.py
```
"""Unit tests for the ``Workflow`` step-by-step state machine.

The aggregate exposes four primary state-changing methods:
``start_at`` → ``record_node_result`` → (``advance_to`` | ``finish`` | ``abort``)

These tests assert:
- valid transitions emit the correct event sequence,
- invalid transitions raise :class:`InvalidWorkflowTransition`,
- the cursor is set/cleared at the right moments,
- ``record_node_result`` does **not** move the cursor.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell_ddd.domain.entities.workflow import Workflow
from shell_ddd.domain.events.events import (
    NodeAdvanced,
    NodeCompleted,
    NodeFailed,
    NodeStarted,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from shell_ddd.domain.exceptions import InvalidWorkflowTransition
from shell_ddd.domain.value_objects.ids import NodeId, NodeResultId, WorkflowId
from shell_ddd.domain.value_objects.status import Status
from shell_ddd.domain.value_objects.workflow_cursor import WorkflowCursor
from shell_ddd.domain.value_objects.workflow_execution_context import (
    WorkflowExecutionContext,
)


_NOW = datetime(2026, 6, 1, tzinfo=UTC)


def _new_workflow() -> Workflow:
    return Workflow.new(id_=WorkflowId.generate(), task_name="t", now=_NOW)


def _ctx() -> WorkflowExecutionContext:
    return WorkflowExecutionContext(work_dir="/tmp", correlation_id="cid-1")


class TestStartAt:
    def test_idle_to_running_sets_cursor_and_emits_events(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)

        assert wf.status == Status.running()
        assert wf.cursor == WorkflowCursor.at(NodeId("n1"))
        assert wf.execution_context == _ctx()

        events = wf.pull_events()
        assert any(isinstance(e, WorkflowStarted) for e in events)
        assert any(isinstance(e, NodeStarted) for e in events)

    def test_double_start_raises(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        with pytest.raises(InvalidWorkflowTransition):
            wf.start_at(first_node_id=NodeId("n2"), context=_ctx(), now=_NOW)


class TestRecordNodeResult:
    def test_recording_does_not_move_cursor(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.pull_events()

        wf.record_node_result(
            result_id=NodeResultId.generate(),
            node_id=NodeId("n1"),
            status=Status.done(),
            now=_NOW,
            stdout="ok",
        )

        assert wf.cursor == WorkflowCursor.at(NodeId("n1"))
        events = wf.pull_events()
        assert any(isinstance(e, NodeCompleted) for e in events)

    def test_recording_failure_emits_node_failed(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.pull_events()

        wf.record_node_result(
            result_id=NodeResultId.generate(),
            node_id=NodeId("n1"),
            status=Status.failed(),
            now=_NOW,
            stderr="boom",
            reason="boom",
        )

        events = wf.pull_events()
        assert any(isinstance(e, NodeFailed) for e in events)


class TestAdvanceTo:
    def test_advance_moves_cursor_and_emits_events(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.record_node_result(
            result_id=NodeResultId.generate(),
            node_id=NodeId("n1"),
            status=Status.done(),
            now=_NOW,
        )
        wf.pull_events()

        wf.advance_to(next_node_id=NodeId("n2"), now=_NOW)

        assert wf.cursor == WorkflowCursor.at(NodeId("n2"))
        events = wf.pull_events()
        assert any(isinstance(e, NodeAdvanced) for e in events)
        assert any(isinstance(e, NodeStarted) for e in events)

    def test_advance_requires_running_status(self) -> None:
        wf = _new_workflow()
        with pytest.raises(InvalidWorkflowTransition):
            wf.advance_to(next_node_id=NodeId("n2"), now=_NOW)

    def test_advance_requires_active_cursor(self) -> None:
        wf = _new_workflow()
        # Reach the otherwise-unreachable "running with no cursor" state by
        # directly mutating the aggregate. This guards against future code
        # paths that might bypass ``start_at`` and leave the cursor empty.
        wf.status = Status.running()
        wf.cursor = WorkflowCursor.empty()
        with pytest.raises(InvalidWorkflowTransition):
            wf.advance_to(next_node_id=NodeId("n2"), now=_NOW)


class TestFinish:
    def test_finish_transitions_to_done_and_clears_cursor(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.record_node_result(
            result_id=NodeResultId.generate(),
            node_id=NodeId("n1"),
            status=Status.done(),
            now=_NOW,
        )
        wf.pull_events()

        wf.finish(_NOW)

        assert wf.status == Status.done()
        assert wf.cursor == WorkflowCursor.empty()
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowCompleted) for e in events)

    def test_finish_from_idle_raises(self) -> None:
        wf = _new_workflow()
        with pytest.raises(InvalidWorkflowTransition):
            wf.finish(_NOW)


class TestAbort:
    def test_abort_transitions_to_failed_and_clears_cursor(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.pull_events()

        wf.abort(reason="boom", now=_NOW)

        assert wf.status == Status.failed()
        assert wf.cursor == WorkflowCursor.empty()
        events = wf.pull_events()
        assert any(isinstance(e, WorkflowFailed) for e in events)

    def test_abort_from_done_raises(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.record_node_result(
            result_id=NodeResultId.generate(),
            node_id=NodeId("n1"),
            status=Status.done(),
            now=_NOW,
        )
        wf.finish(_NOW)
        wf.pull_events()

        with pytest.raises(InvalidWorkflowTransition):
            wf.abort(reason="late", now=_NOW)

    def test_abort_invokes_compensation_handler(self) -> None:
        wf = _new_workflow()
        wf.start_at(first_node_id=NodeId("n1"), context=_ctx(), now=_NOW)
        wf.pull_events()

        called: list[tuple[Workflow, str]] = []

        class _SpyCompensation:
            def compensate(self, workflow: Workflow, reason: str) -> None:
                called.append((workflow, reason))

        wf.abort(reason="boom", now=_NOW, compensation=_SpyCompensation())

        assert called == [(wf, "boom")]
```

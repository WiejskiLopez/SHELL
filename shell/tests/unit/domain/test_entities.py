"""Unit tests for domain entities."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from shell.domain.entities.envelope import Envelope
from shell.domain.entities.task import Task
from shell.domain.entities.workflow import Workflow
from shell.domain.exceptions import InvalidEnvelopeTransition
from shell.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell.domain.value_objects.ids import (
    CorrelationId,
    EnvelopeId,
    NodeId,
    TaskId,
    WorkflowId,
)
from shell.domain.value_objects.task_body import TaskBody
from shell.domain.value_objects.task_name import TaskName
from shell.domain.value_objects.version import Version

if TYPE_CHECKING:
    from shell.domain.entities.rag_document import RagDocument
    from shell.domain.entities.session import Session

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class TestTask:
    def test_create_yields_initial_task(self) -> None:
        task = Task.create(
            id_=TaskId.generate(),
            name=TaskName("task-name"),
            body=TaskBody("task-body"),
            now=_NOW,
        )
        assert task.is_current is True
        assert task.version == Version.initial()
        assert len(task.hash.value) == 64

    def test_create_emits_task_created_event(self) -> None:
        task = Task.create(
            id_=TaskId.generate(),
            name=TaskName("my-task"),
            body=TaskBody("task-body"),
            now=_NOW,
        )
        events = task.pull_events()
        assert len(events) == 1
        assert type(events[0]).__name__ == "TaskCreated"

    def test_hash_changes_with_content(self) -> None:
        t1 = Task.create(
            id_=TaskId.generate(),
            name=TaskName("task-name"),
            body=TaskBody("task-body-a"),
            now=_NOW,
        )
        t2 = Task.create(
            id_=TaskId.generate(),
            name=TaskName("task-name"),
            body=TaskBody("task-body-b"),
            now=_NOW,
        )
        assert t1.hash != t2.hash

    def test_supersede_marks_not_current(self) -> None:
        task = Task.create(
            id_=TaskId.generate(),
            name=TaskName("task-name"),
            body=TaskBody("task-body"),
            now=_NOW,
        )
        task.supersede()
        assert task.is_current is False


class TestWorkflow:
    def test_new_workflow_is_idle(self) -> None:
        wf = Workflow.new(id_=WorkflowId.generate(), task_id=TaskId.generate(), now=_NOW)
        assert wf.status.value == "idle"

    def test_start_at_sets_running(self) -> None:
        from shell.domain.value_objects.workflow_execution_context import (
            WorkflowExecutionContext,
        )

        wf = Workflow.new(id_=WorkflowId.generate(), task_id=TaskId.generate(), now=_NOW)
        wf.start_at(
            first_node_id=NodeId("n1"),
            context=WorkflowExecutionContext.empty(),
            now=_NOW,
        )
        assert wf.status.value == "running"
        assert wf.cursor.current_node_id == NodeId("n1")

    def test_update_node_state(self) -> None:
        from shell.domain.value_objects.status import Status

        wf = Workflow.new(id_=WorkflowId.generate(), task_id="task-id", now=_NOW)
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

    def _make_doc(self) -> RagDocument:
        from shell.domain.entities.rag_document import RagDocument
        from shell.domain.value_objects.ids import RagDocumentId

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
        from shell.domain.value_objects.ids import RagChunkId

        doc = self._make_doc()
        ids = [RagChunkId.generate() for _ in range(3)]
        texts = ["chunk one", "chunk two", "chunk three"]
        embs = [b"\x00" * 4, b"\x00" * 4, b"\x00" * 4]
        doc.add_chunks(ids, texts, embs, "hash-stub")
        assert len(doc.chunks) == 3
        assert doc.chunks[0].chunk_index == 0
        assert doc.chunks[2].chunk_text == "chunk three"

    def test_add_chunks_mismatched_length_raises(self) -> None:
        from shell.domain.value_objects.ids import RagChunkId

        doc = self._make_doc()
        with pytest.raises(ValueError, match="equal length"):
            doc.add_chunks([RagChunkId.generate()], ["a", "b"], [b"\x00" * 4, b"\x00" * 4], "m")

    def test_empty_source_uri_raises(self) -> None:
        from shell.domain.entities.rag_document import RagDocument
        from shell.domain.value_objects.ids import RagDocumentId

        with pytest.raises(ValueError, match="source_uri"):
            RagDocument.new(
                id_=RagDocumentId.generate(), source_uri="", title="T", domain="d", now=self._NOW
            )

    def test_chunk_negative_index_raises(self) -> None:
        from shell.domain.entities.rag_document import RagChunk
        from shell.domain.value_objects.ids import RagChunkId, RagDocumentId

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

    def _make_session(self) -> Session:
        from shell.domain.entities.session import Session
        from shell.domain.value_objects.ids import SessionId

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
        from shell.domain.value_objects.ids import MessageId

        s = self._make_session()
        msg = s.append_message(
            MessageId.generate(),
            CorrelationId.generate(),
            "agent-1",
            "router-1",
            {"text": "hi"},
            self._NOW,
        )
        assert msg.sender == "agent-1"
        assert len(s.messages) == 1

    def test_append_to_closed_session_raises(self) -> None:
        from shell.domain.value_objects.ids import MessageId

        s = self._make_session()
        s.close(self._LATER)
        with pytest.raises(ValueError, match="closed"):
            s.append_message(
                MessageId.generate(), CorrelationId.generate(), "a", "b", {}, self._NOW
            )

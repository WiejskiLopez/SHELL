from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell.domain.messaging.aggregates.message.message import Message
from shell.domain.messaging.aggregates.message.value_objects.materialized_metadata import (
    MaterializedMetadata,
)
from shell.domain.messaging.aggregates.message.value_objects.message_id import MessageId
from shell.domain.messaging.aggregates.message.value_objects.message_status import MessageStatus


class TestMessage:
    def test_new_creates_message_with_created_status(self) -> None:
        now = datetime.now(tz=UTC)
        message = Message.new(
            id_=MessageId.generate(),
            message_type="agent.context.transfer",
            source="planner.node-1",
            destination="tasker.node-2",
            business_payload={"key": "value"},
            metadata={"version": "1.0"},
            now=now,
        )

        assert message.status == MessageStatus.CREATED
        assert message.message_type.value == "agent.context.transfer"
        assert message.source.value == "planner.node-1"
        assert message.destination.value == "tasker.node-2"
        assert message.business_payload.to_dict() == {"key": "value"}
        assert message.metadata.to_dict() == {"version": "1.0"}
        assert message.created_at.value == now
        assert message.received_at is None

    def test_new_generates_message_created_event(self) -> None:
        now = datetime.now(tz=UTC)
        message = Message.new(
            id_=MessageId.generate(),
            message_type="test.event",
            source="src",
            destination="dst",
            now=now,
        )

        events = message.pull_events()
        assert len(events) == 1
        event = events[0]
        assert event.message_id == message.id  # type: ignore[attr-defined]

    def test_mark_as_received_changes_status(self) -> None:
        now = datetime.now(tz=UTC)
        message = Message.new(
            id_=MessageId.generate(),
            message_type="test.receive",
            source="src",
            destination="dst",
            now=now,
        )

        later = datetime.now(tz=UTC)
        message.mark_as_received(later)

        assert message.status == MessageStatus.RECEIVED
        assert message.received_at is not None
        assert message.received_at.value == later

    def test_mark_as_received_emits_event(self) -> None:
        now = datetime.now(tz=UTC)
        message = Message.new(
            id_=MessageId.generate(),
            message_type="test.receive",
            source="src",
            destination="dst",
            now=now,
        )
        message.pull_events()

        later = datetime.now(tz=UTC)
        message.mark_as_received(later)

        events = message.pull_events()
        assert len(events) == 1

    def test_mark_as_received_from_received_raises(self) -> None:
        now = datetime.now(tz=UTC)
        message = Message.new(
            id_=MessageId.generate(),
            message_type="test.invalid",
            source="src",
            destination="dst",
            now=now,
        )
        message.mark_as_received(now)

        with pytest.raises(ValueError, match="received"):
            message.mark_as_received(now)

    def test_materialized_metadata(self) -> None:
        now = datetime.now(tz=UTC)
        mat = MaterializedMetadata(
            workflow_id="wf-1",
            step=2,
            sequence_id=3,
            source_node_execution_id="src-node-1",
            target_node_execution_id="tgt-node-2",
            source_role="planner",
            target_role="tasker",
        )
        message = Message.new(
            id_=MessageId.generate(),
            message_type="test.execution",
            source="src",
            destination="dst",
            materialized_metadata=mat,
            now=now,
        )

        assert message.materialized_metadata.workflow_id == "wf-1"
        assert message.materialized_metadata.step == 2
        assert message.materialized_metadata.sequence_id == 3
        assert message.materialized_metadata.source_role == "planner"
        assert message.materialized_metadata.target_role == "tasker"

    def test_restore_preserves_all_fields(self) -> None:
        now = datetime.now(tz=UTC)
        datetime.now(tz=UTC)
        msg_id = MessageId.generate()

        original = Message.new(
            id_=msg_id,
            message_type="test.restore",
            source="src",
            destination="dst",
            business_payload={"data": 1},
            metadata={"meta": "x"},
            now=now,
        )
        original.pull_events()  # clear events

        restored = Message.restore(
            id=msg_id,
            message_type=original.message_type,
            business_payload=original.business_payload,
            metadata=original.metadata,
            source=original.source,
            destination=original.destination,
            status=original.status,
            materialized_metadata=original.materialized_metadata,
            created_at=original.created_at,
            received_at=None,
        )

        assert restored.id == original.id
        assert restored.message_type == original.message_type
        assert restored.business_payload == original.business_payload
        assert restored.metadata == original.metadata
        assert restored.source == original.source
        assert restored.destination == original.destination
        assert restored.status == original.status
        assert restored.created_at == original.created_at

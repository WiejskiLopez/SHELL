"""Faza 4 tests — PayloadUpcaster and version-aware deserialization."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.execution_service.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
    TaskExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.serialization.event_deserializer import EventDeserializer
from shell.platform.infrastructure.serialization.upcaster import PayloadTransform, PayloadUpcaster


def _transform(fn: PayloadTransform) -> PayloadTransform:
    return fn


def _occurred_at() -> OccurredAt:
    return OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC))


def _occurred_at_value() -> datetime:
    return _occurred_at().value


def _event_id() -> TaskExecutionId:
    return TaskExecutionId.generate()


class TestPayloadUpcaster:
    def test_applies_full_chain_and_returns_final_version(self) -> None:
        upcaster = PayloadUpcaster(
            {
                "SomeEvent": {
                    1: _transform(lambda p: {**p, "b": "v1->v2"}),
                    2: _transform(lambda p: {**p, "c": "v2->v3"}),
                }
            }
        )

        payload, version = upcaster.upcast("SomeEvent", 1, {"a": 1})

        assert version == 3
        assert payload == {"a": 1, "b": "v1->v2", "c": "v2->v3"}

    def test_no_transform_leaves_payload_untouched(self) -> None:
        upcaster = PayloadUpcaster({})

        payload, version = upcaster.upcast("SomeEvent", 1, {"a": 1})

        assert version == 1
        assert payload == {"a": 1}

    def test_chain_stops_when_no_next_transform(self) -> None:
        upcaster = PayloadUpcaster({"SomeEvent": {1: _transform(lambda p: {**p, "x": 1})}})

        payload, version = upcaster.upcast("SomeEvent", 2, {"a": 1})

        assert version == 2
        assert payload == {"a": 1}


class TestVersionAwareDeserialization:
    def test_event_deserializer_upcasts_older_schema(self) -> None:
        """A v1 payload (task_execution_id as raw str) is upcast to v2 shape."""
        task_id = _event_id()
        v1_payload: dict[str, object] = {"task_execution_id": str(task_id.value)}

        upcaster = PayloadUpcaster(
            {
                TaskExecutionCreatedEvent.__name__: {
                    1: _transform(
                        lambda p: {
                            "task_execution_id": TaskExecutionId(str(p["task_execution_id"]))
                        }
                    ),
                }
            }
        )
        deserializer = EventDeserializer(
            registry={TaskExecutionCreatedEvent.__name__: TaskExecutionCreatedEvent},
            upcaster=upcaster,
        )

        event = deserializer.deserialize(
            TaskExecutionCreatedEvent.__name__,
            _occurred_at_value(),
            v1_payload,
            schema_version=1,
        )

        assert isinstance(event, TaskExecutionCreatedEvent)
        assert event.task_execution_id == task_id

    def test_unknown_event_type_returns_none(self) -> None:
        deserializer = EventDeserializer(registry={})

        result = deserializer.deserialize(
            "MissingEvent", _occurred_at_value(), {}, schema_version=1
        )

        assert result is None

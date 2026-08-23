"""Unit tests — DomainMessage content-delivery contract.

Message is addressed point-to-point, never broadcast. It always carries
``state_data`` (a validated JSON string — at most an empty JSON object, never
``None``) and always resolves a concrete recipient aggregate: one that owns
``_state_data``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from shell.platform.domain.exceptions import DomainError
from shell.platform.domain.messages import DomainMessage
from shell.platform.domain.value_objects.aggregate_id import AggregateId
from shell.platform.domain.value_objects.aggregate_name import AggregateName
from shell.platform.domain.value_objects.message_id import MessageId
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.schema_version import SchemaVersion
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.infrastructure.serialization.message.domain_message_serializer import (
    DomainMessageSerializer,
)
from shell.platform.infrastructure.serialization.payload.payload_object_deserializer import (
    PayloadObjectDeserializer,
)
from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True, kw_only=True)
class _ContentMessage(DomainMessage):
    pass


_STATE_DATA = StateData(JsonStr.from_object({"priority": 1}))


def _occurred_at() -> OccurredAt:
    return OccurredAt.from_datetime(datetime(2026, 1, 1, tzinfo=UTC))


def _content_message(**overrides: object) -> _ContentMessage:
    defaults: dict[str, object] = {
        "occurred_at": _occurred_at(),
        "recipient_aggregate_id": AggregateId("agent-1"),
        "recipient_aggregate_name": AggregateName("Agent"),
        "state_data": _STATE_DATA,
    }
    defaults.update(overrides)
    return _ContentMessage(**defaults)  # type: ignore[arg-type]


class TestContentContract:
    def test_partial_recipient_is_rejected(self) -> None:
        with pytest.raises(DomainError, match="must both be set or both be None"):
            _content_message(recipient_aggregate_name=None)

    def test_state_data_is_never_none(self) -> None:
        message = _content_message()
        assert message.state_data is not None

    def test_state_data_is_always_json(self) -> None:
        message = _content_message(state_data=StateData(JsonStr.from_object({})))
        assert message.state_data.value.value == "{}"

    def test_invalid_json_is_rejected_by_json_str(self) -> None:
        with pytest.raises(ValueError, match="not valid JSON"):
            _content_message(state_data=StateData(JsonStr("not-json")))

    def test_addressed_state_message_is_valid(self) -> None:
        message = _content_message()
        assert message.recipient_aggregate_id is not None
        assert message.recipient_aggregate_name is not None
        assert message.recipient_aggregate_id.value == "agent-1"
        assert message.recipient_aggregate_name.value == "Agent"
        assert message.state_data == _STATE_DATA

    def test_recipient_and_state_data_survive_serializer_round_trip(self) -> None:
        message = _content_message(
            message_id=MessageId.generate(),
            occurred_at=_occurred_at(),
            state_data=StateData(JsonStr.from_object({"role": "worker", "active": True})),
        )
        payload = DomainMessageSerializer().to_payload(message)
        restored = PayloadObjectDeserializer().deserialize(
            object_cls=_ContentMessage,
            occurred_at=message.occurred_at.value,
            payload=payload,
            schema_version=1,
        )
        assert isinstance(restored, _ContentMessage)
        assert restored.recipient_aggregate_id is not None
        assert restored.recipient_aggregate_name is not None
        assert str(restored.recipient_aggregate_id.value) == "agent-1"
        assert str(restored.recipient_aggregate_name.value) == "Agent"
        assert restored.state_data.value.value == '{"role": "worker", "active": true}'
        assert restored.schema_version == SchemaVersion(1)

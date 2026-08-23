"""Unit tests — IntegrationMessage content-delivery contract.

Cross-BC ``IntegrationMessage`` carries the same invariants as ``DomainMessage``:
serialized ``state_data`` (JSON via ``JsonStr``, never ``None``) bound to a
concrete recipient aggregate (one that owns ``_state_data``).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell.platform.application.messages import IntegrationMessage
from shell.platform.domain.exceptions import DomainError
from shell.platform.types import JsonStr


def _integration_message(**overrides: object) -> IntegrationMessage:
    defaults: dict[str, object] = {
        "message_id": "msg-1",
        "correlation_id": "corr-1",
        "causation_id": "cause-1",
        "occurred_at": datetime(2026, 1, 1, tzinfo=UTC),
        "aggregate_id": "source-1",
        "aggregate_name": "Ingestion",
        "schema_version": 2,
        "recipient_aggregate_id": "agent-1",
        "recipient_aggregate_name": "Agent",
        "state_data": JsonStr.from_object({"priority": 1}),
    }
    defaults.update(overrides)
    return IntegrationMessage(**defaults)  # type: ignore[arg-type]


class TestContentContract:
    def test_partial_recipient_is_rejected(self) -> None:
        with pytest.raises(DomainError, match="must both be set or both be None"):
            _integration_message(recipient_aggregate_id=None)

    def test_state_data_is_never_none(self) -> None:
        assert _integration_message().state_data is not None

    def test_state_data_is_always_json(self) -> None:
        message = _integration_message(state_data=JsonStr.from_object({}))
        assert message.state_data.value == "{}"

    def test_invalid_json_is_rejected_by_json_str(self) -> None:
        with pytest.raises(ValueError, match="not valid JSON"):
            _integration_message(state_data=JsonStr("not-json"))

    def test_addressed_state_message_is_valid(self) -> None:
        message = _integration_message()
        assert message.recipient_aggregate_id == "agent-1"
        assert message.recipient_aggregate_name == "Agent"
        assert message.state_data == JsonStr.from_object({"priority": 1})

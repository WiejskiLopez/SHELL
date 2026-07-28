"""Tests for ReflectiveIntegrationMapper."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell.domain.execution.aggregates.node_execution.events.node_execution_created_event import (
    NodeExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.session_execution.events.session_execution_created_event import (
    SessionExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.domain.session.aggregates.session.events.session_opened_event import SessionOpenedEvent
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.value_objects.user_id_ref import UserIdRef
from shell.domain.user.aggregates.user.events.user_login_succeeded_event import (
    UserLoginSucceededEvent,
)
from shell.domain.user.value_objects.user_id import UserId
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.infrastructure.mapping.reflective_integration_mapper import (
    ReflectiveIntegrationMapper,
)

_NOW = OccurredAt.from_datetime(datetime(2025, 1, 1, tzinfo=UTC))


class TestReflectiveIntegrationMapper:
    def setup_method(self) -> None:
        self._mapper = ReflectiveIntegrationMapper()

    def test_map_session_opened(self) -> None:
        event = SessionOpenedEvent.now(
            session_id=SessionId.generate(),
            user_id=UserIdRef.generate(),
            now=_NOW,
        )
        result: object = self._mapper.map(event)
        assert type(result).__name__ == "SessionOpenedIntegrationEvent"
        assert result.session_id == event.session_id.value  # type: ignore[attr-defined]
        assert result.user_id == event.user_id.value  # type: ignore[attr-defined]

    def test_map_user_login_succeeded(self) -> None:
        event = UserLoginSucceededEvent.now(
            user_id=UserId.generate(),
            now=_NOW,
        )
        result: object = self._mapper.map(event)
        assert type(result).__name__ == "UserLoginSucceededIntegrationEvent"
        assert result.user_id == event.user_id.value  # type: ignore[attr-defined]

    def test_map_event_with_nullable_fields(self) -> None:
        event = NodeExecutionCreatedEvent.now(
            node_execution_id=NodeExecutionId.generate(),
            node_definition_id=None,
            graph_execution_id=None,
            now=_NOW,
        )
        result: object = self._mapper.map(event)
        assert type(result).__name__ == "NodeExecutionCreatedIntegrationEvent"
        assert result.node_execution_id == event.node_execution_id.value  # type: ignore[attr-defined]
        assert result.node_definition_id is None  # type: ignore[attr-defined]
        assert result.graph_execution_id is None  # type: ignore[attr-defined]

    def test_map_session_execution_created(self) -> None:
        event = SessionExecutionCreatedEvent.now(
            session_execution_id=SessionExecutionId.generate(),
            now=_NOW,
        )
        result: object = self._mapper.map(event)
        assert type(result).__name__ == "SessionExecutionCreatedIntegrationEvent"
        assert result.session_execution_id == event.session_execution_id.value  # type: ignore[attr-defined]

    def test_unknown_event_type_raises(self) -> None:
        class FakeEvent:
            __module__ = "shell.domain.fake.aggregates.fake.events.fake_event"
            __name__ = "FakeEvent"
            event_id = type("id", (), {"value": "x"})()
            occurred_at = type("oa", (), {"value": datetime(2025, 1, 1, tzinfo=UTC)})()
            aggregate_id = type("id", (), {"value": ""})()
            aggregate_name = type("n", (), {"value": ""})()
            schema_version = type("v", (), {"value": 1})()

        with pytest.raises(ValueError, match="Cannot find integration event"):
            self._mapper.map(FakeEvent())

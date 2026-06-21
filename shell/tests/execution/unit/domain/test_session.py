"""Unit tests for Session entity."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from shell.domain.execution.entities.session import Session
from shell.domain.execution.value_objects.ids import MessageId, SessionId
from shell.domain.platform.value_objects.ids import CorrelationId

_NOW = datetime(2025, 1, 1, tzinfo=UTC)
_LATER = datetime(2025, 1, 2, tzinfo=UTC)


class TestSession:
    def _make_session(self) -> Session:
        return Session.open(id_=SessionId.generate(), goal="do stuff", now=_NOW)

    def test_open_creates_open_session(self) -> None:
        s = self._make_session()
        assert s.status == "open"
        assert s.closed_at is None
        assert s.messages == []

    def test_close_sets_status_and_closed_at(self) -> None:
        s = self._make_session()
        s.close(_LATER)
        assert s.status == "closed"
        assert s.closed_at == _LATER

    def test_close_twice_raises(self) -> None:
        s = self._make_session()
        s.close(_LATER)
        with pytest.raises(ValueError, match="already closed"):
            s.close(_LATER)

    def test_append_message(self) -> None:
        s = self._make_session()
        msg = s.append_message(
            MessageId.generate(),
            CorrelationId.generate(),
            "agent-1",
            "router-1",
            {"text": "hi"},
            _NOW,
        )
        assert msg.sender == "agent-1"
        assert len(s.messages) == 1

    def test_append_to_closed_session_raises(self) -> None:
        s = self._make_session()
        s.close(_LATER)
        with pytest.raises(ValueError, match="closed"):
            s.append_message(
                MessageId.generate(), CorrelationId.generate(), "a", "b", {}, _NOW
            )

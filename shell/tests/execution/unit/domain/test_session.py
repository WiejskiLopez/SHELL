"""Unit tests for Session entity."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.domain.session.aggregates.session import Session
from shell.domain.session.aggregates.session.exceptions.invalid_session_transition import (
    InvalidSessionTransition,
)
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId

_NOW = CreatedAt.from_datetime(datetime(2025, 1, 1, tzinfo=UTC))
_LATER = UpdatedAt.from_datetime(datetime(2025, 1, 2, tzinfo=UTC))


class TestSession:
    def _make_session(self) -> Session:
        return Session.open(id_=SessionId.generate(), goal="do stuff", now=_NOW)

    def test_open_creates_open_session(self) -> None:
        s = self._make_session()
        assert s.status == "open"
        assert s.closed_at is None

    def test_close_sets_status_and_closed_at(self) -> None:
        s = self._make_session()
        s.close(_LATER)
        assert s.status == "closed"
        assert s.closed_at == _LATER

    def test_close_twice_raises(self) -> None:
        s = self._make_session()
        s.close(_LATER)
        with pytest.raises(InvalidSessionTransition, match="Cannot close session"):
            s.close(_LATER)

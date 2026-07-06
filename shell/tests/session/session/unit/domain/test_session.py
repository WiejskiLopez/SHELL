"""Unit tests for Session entity."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.domain.session.aggregates.session import Session
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId

_NOW = CreatedAt.from_datetime(datetime(2025, 1, 1, tzinfo=UTC))
_LATER_DT = UpdatedAt.from_datetime(datetime(2025, 1, 2, tzinfo=UTC))


class TestSession:
    def _make_session(self) -> Session:
        return Session.open(id_=SessionId.generate(), goal="do stuff", now=_NOW)

    def test_open_creates_open_session(self) -> None:
        s = self._make_session()
        assert s.status == "open"

    def test_close_sets_closed_at(self) -> None:
        s = self._make_session()
        s.close(_LATER_DT)
        assert s.closed_at == _LATER_DT

    def test_close_twice_raises(self) -> None:
        s = self._make_session()
        s.close(_LATER_DT)
        import pytest

        with pytest.raises(ValueError):
            s.close(UpdatedAt.from_datetime(datetime(2025, 1, 3, tzinfo=UTC)))

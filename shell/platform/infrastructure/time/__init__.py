"""System clock and UUID-based ID generator."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    """Real wall-clock implementation of Clock port."""

    def now(self) -> datetime:
        return datetime.now(tz=UTC)

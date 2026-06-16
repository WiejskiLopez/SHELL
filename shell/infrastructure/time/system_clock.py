"""SystemClock — real wall-clock implementation of the Clock port."""

from __future__ import annotations

from datetime import UTC, datetime


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(tz=UTC)

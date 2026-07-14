"""SQL ORM model <-> domain entity mapper for GraphExecutionState aggregate."""

from __future__ import annotations

from datetime import UTC, datetime


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

